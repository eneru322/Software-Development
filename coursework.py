# ==============================================================
#  Final Grade Calculator
# ==============================================================

import re
from datetime import date, datetime

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None
    print("Warning: 'tabulate' is not installed (pip install tabulate). "
          "A simple table format will be used instead.")





# ==============================================================
#  SETTINGS (values that do not change while the program runs)
# ==============================================================

OUTPUT_FILE = "students.txt"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

MAX_COURSEWORKS = 10
MAX_AGE = 100

HEADERS = ["ID", "First Name", "Surname", "Date of Birth",
           "Age", "Overall Mark", "Grade", "Result Time"]

# Allowed final marks: the overall mark is rounded to the closest one
ROUNDING_VALUES = [
    0, 5, 15, 25, 32, 35, 38, 42, 45, 48,
    52, 55, 58, 62, 65, 68, 72, 75, 78,
    82, 85, 92, 100
]





# Grade categories: which rounded marks give which grade
# (any other mark, e.g. 0, 5, 15, 25, is a Fail)
GRADE_CATEGORIES = [
    ([100],          "Gold Standard"),
    ([82, 85, 92],   "Upper First"),
    ([72, 75, 78],   "First"),
    ([62, 65, 68],   "Upper Second"),
    ([52, 55, 58],   "Lower Second"),
    ([42, 45, 48],   "Third"),
    ([32, 35, 38],   "Condonable Fail"),
]





# ==============================================================
#  STEP 1 FUNCTIONS: load students.txt and fix mistakes in it
# ==============================================================

# Load students that were saved in earlier runs from the table in the file
# (rows are loaded as they are; check_and_fix_students() checks them later)
def load_students(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.read().splitlines()
    except FileNotFoundError:
        return []

    table_lines = [line for line in lines if line.startswith("|")]
    if not table_lines:
        return []

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    loaded = []

    for line_number, line in enumerate(table_lines[1:], start=2):
        cells = [cell.strip() for cell in line.strip("|").split("|")]

        if len(cells) != len(headers):
            print(f"File check: table row {line_number} is broken "
                  f"(wrong number of columns) and was removed.")
            continue

        row = dict(zip(headers, cells))
        loaded.append({h: row.get(h, "") for h in HEADERS})

    return loaded





# Calculate age in full years
def calculate_age(birth_date, today):
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )




# Fix a name from the file: remove wrong symbols and capitalise it.
# Returns None if nothing usable is left.
def fix_name(name):
    cleaned = "".join(ch for ch in name if ch.isalpha() or ch in "-'")
    cleaned = re.sub(r"[-']{2,}", "-", cleaned).strip("-'")

    if not 2 <= len(cleaned) <= 30:
        return None

    return re.sub(
        r"[^\W\d_]+",
        lambda m: m.group(0).capitalize(),
        cleaned.lower()
    )





# Fix a date of birth from the file.
# Accepts YYYY-MM-DD and also common wrong formats (2004/09/15,
# 15.09.2004 ...). Returns the date as YYYY-MM-DD, or None if it is wrong.
def fix_birth_date(value):
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
               "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"]
    value = value.replace(" ", "")
    today = date.today()

    for date_format in formats:
        try:
            birth_date = datetime.strptime(value, date_format).date()
        except ValueError:
            continue

        if birth_date <= today and calculate_age(birth_date, today) <= MAX_AGE:
            return birth_date.isoformat()
        return None

    return None




# Fix an overall mark from the file: it must be one of ROUNDING_VALUES.
# A number between 0 and 100 is rounded to the closest allowed value.
def fix_mark(value):
    try:
        number = float(value)
    except ValueError:
        return None

    if not 0 <= number <= 100:
        return None

    return round_mark(number)





# Check every student loaded from the file and fix the problems.
# Returns the fixed list and a list of messages about what was fixed.
def check_and_fix_students(loaded):
    messages = []
    today = date.today()

    # 1) IDs: keep the first valid unique ID, collect the others
    taken = set()
    need_new_id = []

    for student in loaded:
        old_id = student["ID"]
        student_id = old_id.zfill(2) if old_id.isascii() and old_id.isdigit() else old_id

        if not (student_id.isascii() and student_id.isdigit() and len(student_id) == 2):
            messages.append(f"ID '{old_id}' is not 2 digits.")
            need_new_id.append(student)
        elif student_id in taken:
            messages.append(f"ID {student_id} is used more than once.")
            need_new_id.append(student)
        else:
            if student_id != old_id:
                messages.append(f"ID '{old_id}' changed to {student_id}.")
            student["ID"] = student_id
            taken.add(student_id)

    # Give the next free ID to every student that needs one
    free_ids = [f"{n:02d}" for n in range(100) if f"{n:02d}" not in taken]

    for student in need_new_id:
        if not free_ids:
            messages.append(f"No free IDs left: student "
                            f"{student['First Name']} {student['Surname']} removed.")
            loaded.remove(student)
            continue

        new_id = free_ids.pop(0)
        messages.append(f"Student {student['First Name']} {student['Surname']} "
                        f"got the new free ID {new_id}.")
        student["ID"] = new_id
        taken.add(new_id)

    # 2) The other columns
    for student in loaded:
        sid = student["ID"]

        # First name and surname
        for field in ["First Name", "Surname"]:
            fixed = fix_name(student[field])
            if fixed is None:
                messages.append(f"ID {sid}: {field} '{student[field]}' is wrong, "
                                f"set to 'Unknown'.")
                fixed = "Unknown"
            elif fixed != student[field]:
                messages.append(f"ID {sid}: {field} '{student[field]}' "
                                f"fixed to '{fixed}'.")
            student[field] = fixed

        # Date of birth and age
        fixed_date = fix_birth_date(student["Date of Birth"])
        if fixed_date is None:
            if student["Date of Birth"] != "Unknown":
                messages.append(f"ID {sid}: date of birth "
                                f"'{student['Date of Birth']}' is wrong, "
                                f"set to 'Unknown'.")
            student["Date of Birth"] = "Unknown"
            student["Age"] = "Unknown"
        else:
            if fixed_date != student["Date of Birth"]:
                messages.append(f"ID {sid}: date of birth "
                                f"'{student['Date of Birth']}' fixed to {fixed_date}.")
            student["Date of Birth"] = fixed_date

            # Age is always calculated again from the date of birth
            age = calculate_age(date.fromisoformat(fixed_date), today)
            if student["Age"] != str(age):
                messages.append(f"ID {sid}: age '{student['Age']}' "
                                f"fixed to {age}.")
            student["Age"] = age

        # Overall mark and grade
        fixed_mark = fix_mark(student["Overall Mark"])
        if fixed_mark is None:
            if student["Overall Mark"] != "Unknown":
                messages.append(f"ID {sid}: overall mark "
                                f"'{student['Overall Mark']}' is wrong, "
                                f"set to 'Unknown'.")
            student["Overall Mark"] = "Unknown"
            student["Grade"] = "Unknown"
        else:
            if str(fixed_mark) != student["Overall Mark"]:
                messages.append(f"ID {sid}: overall mark "
                                f"'{student['Overall Mark']}' fixed to {fixed_mark}.")
            student["Overall Mark"] = fixed_mark

            # Grade is always worked out again from the mark
            grade = get_grade(fixed_mark)
            if student["Grade"] != grade:
                messages.append(f"ID {sid}: grade '{student['Grade']}' "
                                f"fixed to '{grade}'.")
            student["Grade"] = grade

        # Result time
        try:
            datetime.strptime(student["Result Time"], TIME_FORMAT)
        except ValueError:
            if student["Result Time"] != "Unknown":
                messages.append(f"ID {sid}: result time "
                                f"'{student['Result Time']}' is wrong, "
                                f"set to 'Unknown'.")
            student["Result Time"] = "Unknown"

    loaded.sort(key=lambda st: int(st["ID"]))
    return loaded, messages






# ==============================================================
#  STEP 2 FUNCTION: how many courseworks
# ==============================================================

# Ask how many courseworks there are (1 to MAX_COURSEWORKS)
def get_coursework_count():
    while True:
        value = input(
            f"How many courseworks are there? (1-{MAX_COURSEWORKS}): "
        ).strip()

        if not (value.isascii() and value.isdigit()):
            print("Error: Enter a whole number, such as 3.")
        elif not 1 <= int(value) <= MAX_COURSEWORKS:
            print(f"Error: Enter a number from 1 to {MAX_COURSEWORKS}.")
        else:
            return int(value)





# ==============================================================
#  STEP 3 FUNCTION: percentages (also used for the marks in step 5)
# ==============================================================

# Get a number between 0 and 100
def get_percentage(prompt):
    while True:
        value = input(prompt).strip()

        try:
            number = float(value)
        except ValueError:
            print("Error: Please enter numbers only.")
            continue

        if 0 <= number <= 100:
            return number

        print("Error: Enter a number between 0 and 100.")






# ==============================================================
#  STEP 4 FUNCTION: how many students
# ==============================================================

# Get a valid positive integer (not more than the number of free IDs)
def get_student_count(free_ids):
    while True:
        value = input("Enter the number of students: ").strip()

        if not (value.isascii() and value.isdigit() and int(value) > 0):
            print("Error: Enter a positive whole number, such as 3.")
        elif int(value) > free_ids:
            print(f"Error: Only {free_ids} free IDs are left (00-99).")
        else:
            return int(value)







# ==============================================================
#  STEP 5 FUNCTIONS: questions about each student
# ==============================================================

# Get a valid student ID: exactly 2 digits (00-99), unique
def get_student_id(used_ids):
    while True:
        student_id = input("Enter student ID (2 digits, e.g. 07): ")

        if student_id != student_id.strip() or " " in student_id:
            print("Error: ID must not contain spaces.")
        elif student_id == "":
            print("Error: ID cannot be empty.")
        elif not (student_id.isascii() and student_id.isdigit()):
            print("Error: ID must contain digits only (no letters or symbols).")
        elif len(student_id) != 2:
            print("Error: ID must be exactly 2 digits.")
        elif student_id in used_ids:
            print(f"Error: ID {student_id} is already used. Enter another one.")
        else:
            return student_id




# Get a valid first name or surname
# Letters only; a single hyphen or apostrophe is allowed between letters
# (e.g. Anne-Marie, O'Neil). No spaces, digits or other symbols.
def get_name(prompt):
    pattern = re.compile(r"^[^\W\d_]+(?:[-'][^\W\d_]+)*$")

    while True:
        name = input(prompt)

        if name.strip() == "":
            print("Error: This field cannot be empty.")
        elif " " in name or "\t" in name:
            print("Error: Spaces are not allowed.")
        elif any(ch.isdigit() for ch in name):
            print("Error: Digits are not allowed.")
        elif len(name) < 2:
            print("Error: Must contain at least 2 letters.")
        elif len(name) > 30:
            print("Error: Must be 30 characters or fewer.")
        elif not pattern.match(name):
            print("Error: Use letters only (a hyphen or apostrophe "
                  "is allowed between letters).")
        else:
            # Capitalise each part: "anne-marie" -> "Anne-Marie"
            return re.sub(
                r"[^\W\d_]+",
                lambda m: m.group(0).capitalize(),
                name.lower()
            )


# Get a valid date of birth in the format YYYY-MM-DD
def get_birth_date():
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    while True:
        value = input("Enter date of birth (YYYY-MM-DD): ")

        if value.strip() == "":
            print("Error: Date of birth cannot be empty.")
            continue

        if " " in value:
            print("Error: Spaces are not allowed.")
            continue

        if not (value.isascii() and pattern.match(value)):
            print("Error: Use the format YYYY-MM-DD with digits only, "
                  "e.g. 2004-09-15.")
            continue

        try:
            birth_date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            print("Error: This date does not exist "
                  "(check the month 01-12 and the day for that month).")
            continue

        today = date.today()

        if birth_date > today:
            print("Error: Date of birth cannot be in the future.")
            continue

        age = calculate_age(birth_date, today)

        if age > MAX_AGE:
            print(f"Error: Age cannot be more than {MAX_AGE} years.")
            continue

        return birth_date.isoformat(), age






# ==============================================================
#  STEP 6 FUNCTIONS: maths (rounding + grade category)
# ==============================================================

# Round a mark to the closest value in ROUNDING_VALUES.
# If two values are equally close, choose the higher one(+2).
def round_mark(mark):
    return min(
        ROUNDING_VALUES,
        key=lambda value: (abs(mark - value), -value)
    )


# Find the grade category for a rounded mark (uses GRADE_CATEGORIES)
def get_grade(rounded_mark):
    for marks, grade in GRADE_CATEGORIES:
        if rounded_mark in marks:
            return grade
    return "Fail"





# ==============================================================
#  STEP 7 AND 8 FUNCTIONS: table (tabulate) and saving
# ==============================================================

# Build a text table (tabulate if available, otherwise a simple fallback)
def make_table(rows, headers):
    if tabulate is not None:
        return tabulate(rows, headers=headers, tablefmt="grid",
                        disable_numparse=True)

    widths = [
        max(len(str(x)) for x in col)
        for col in zip(headers, *rows)
    ]
    line = "+-" + "-+-".join("-" * w for w in widths) + "-+"

    def fmt(row):
        return "| " + " | ".join(
            str(x).ljust(w) for x, w in zip(row, widths)
        ) + " |"

    out = [line, fmt(headers), line.replace("-", "=")]
    for row in rows:
        out.append(fmt(row))
        out.append(line)
    return "\n".join(out)


# Make the table of all students, sorted by ID
def students_table(students):
    rows = [[st[h] for h in HEADERS] for st in students]
    return make_table(rows, HEADERS)


# Save all students to the file as a table sorted by ID
def save_students(students):
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write("Student Final Results (sorted by ID)\n")
            file.write(f"Generated: {datetime.now().strftime(TIME_FORMAT)}\n\n")
            file.write(students_table(students))
            file.write("\n")
        return True
    except OSError as error:
        print(f"Error: Could not save {OUTPUT_FILE}: {error}")
        return False





# ==============================================================
#  MAIN PROGRAM (runs from here, step by step)
# ==============================================================



# ---------- STEP 1: load students.txt and check it for mistakes ----------
students = load_students(OUTPUT_FILE)
students, fix_messages = check_and_fix_students(students)

if fix_messages:
    print(f"File check: {len(fix_messages)} problem(s) found in {OUTPUT_FILE}:")
    for message in fix_messages:
        print("  -", message)
    if save_students(students):
        print(f"File check: the fixed table was saved to {OUTPUT_FILE}.\n")
elif students:
    print(f"File check: no problems found in {OUTPUT_FILE}.")

used_ids = {s["ID"] for s in students}

if students:
    print(f"Loaded {len(students)} student(s) from {OUTPUT_FILE}. "
          f"Taken IDs: {', '.join(sorted(used_ids))}\n")

if len(used_ids) >= 100:
    print("Error: All IDs 00-99 are already used. No new students can be added.")
    raise SystemExit






# ---------- STEP 2: how many courseworks ----------
# (the Final Test is always added at the end)
coursework_count = get_coursework_count()

coursework_names = []
for number in range(1, coursework_count + 1):
    coursework_names.append(f"Coursework {number}")
coursework_names.append("Final Test")






# ---------- STEP 3: percentage of each work (must total 100%) ----------
while True:
    coursework_percentages = []

    for name in coursework_names:
        percentage = get_percentage(f"How many % is {name} worth? ")
        coursework_percentages.append(percentage / 100)

    total_percentage = sum(coursework_percentages)

    if abs(total_percentage - 1.0) < 0.000001:
        break

    print(
        f"Error: The percentages total {total_percentage * 100:g}%. "
        "They must add up to 100%. Please enter them again."
    )





# ---------- STEP 4: how many students ----------
number_of_students = get_student_count(100 - len(used_ids))





# ---------- STEP 5 + 6: each student's data, then the maths ----------
for i in range(number_of_students):
    print(f"\nEnter data for student {i + 1}")

    # Step 5: questions about the student
    student_id = get_student_id(used_ids)
    used_ids.add(student_id)

    first_name = get_name("Enter first name: ")
    last_name = get_name("Enter surname: ")
    birth_date, age = get_birth_date()

    marks = []
    for name in coursework_names:
        marks.append(get_percentage(f"Enter mark for {name}: "))

    # Step 6: maths - weighted total, rounding, grade category
    all_result = 0
    for j in range(len(coursework_names)):
        all_result += marks[j] * coursework_percentages[j]

    rounded_mark = round_mark(all_result)
    grade = get_grade(rounded_mark)

    students.append({
        "ID": student_id,
        "First Name": first_name,
        "Surname": last_name,
        "Date of Birth": birth_date,
        "Age": age,
        "Overall Mark": rounded_mark,
        "Grade": grade,
        "Result Time": datetime.now().strftime(TIME_FORMAT)
    })




# ---------- STEP 7: show the results as a table (tabulate) ----------
students.sort(key=lambda s: int(s["ID"]))

print("\n--- Student Final Results (sorted by ID) ---")
print(students_table(students))





# ---------- STEP 8: save the table to students.txt ----------
if save_students(students):
    print(f"\nResults saved to {OUTPUT_FILE}")
