import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

#Constants
WINDOW_TITLE = "Student Manager"
WINDOW_SIZE = "900x600"
#Build the path from this script's location so it works from any folder
DATA_FILE = Path(__file__).parent / "studentMarks.txt"
#Maximum marks available (3 coursework marks of 20, plus an exam out of 100)
MAX_COURSEWORK_MARK = 20
MAX_EXAM_MARK = 100
COURSEWORK_COUNT = 3
MAX_TOTAL = COURSEWORK_COUNT * MAX_COURSEWORK_MARK + MAX_EXAM_MARK #160
#Valid range for a student code, and the number of comma-separated fields
MIN_CODE = 1000
MAX_CODE = 9999
FIELDS_PER_LINE = COURSEWORK_COUNT + 3
# Maximum number of file problems listed in the warning popup
MAX_PROBLEMS_SHOWN = 5
#Grade boundaries: minimum percentage, grade, checked from highest to lowest
GRADE_BOUNDARIES = [(70, "A"), (60, "B"), (50, "C"), (40, "D"), (0, "F")]

class Student:

    def __init__(self, code, name, coursework, exam):
        self.code = code
        self.name = name
        self.coursework = coursework
        self.exam = exam   

    @property
    def coursework_total(self):
        return sum(self.coursework)

    @property
    def total(self):
        return self.coursework_total + self.exam

    @property
    def percentage(self):
        return self.total / MAX_TOTAL * 100

    @property
    def grade(self):
        for minimum, grade in GRADE_BOUNDARIES:
            if self.percentage >= minimum:
                return grade   

    def __str__(self):
        return (f"{self.code} {self.name}: {self.total}/{MAX_TOTAL} " f"({self.percentage:.1f}%) grade {self.grade}")

def parseStudent(line):
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != FIELDS_PER_LINE:
        raise ValueError(f"expected {FIELDS_PER_LINE} fields but found {len(parts)}")

    code_text, name, *mark_texts = parts

    code = int(code_text)
    if not MIN_CODE <= code <= MAX_CODE:
        raise ValueError(f"code {code} is not between {MIN_CODE} and {MAX_CODE}")

    if not name:
        raise ValueError("the student name is empty")

    #The first three marks are coursework, the last one is the exam
    coursework = [int(mark) for mark in mark_texts[:COURSEWORK_COUNT]]
    exam = int(mark_texts[-1])

    if any(not 0 <= mark <= MAX_COURSEWORK_MARK for mark in coursework):
        raise ValueError(f"coursework marks must be 0-{MAX_COURSEWORK_MARK}")
    if not 0 <= exam <= MAX_EXAM_MARK:
        raise ValueError(f"the exam mark must be 0-{MAX_EXAM_MARK}")

    return Student(code, name, coursework, exam)

def loadStudents(path):
    students = []
    problems = []
    codes_seen = set()
    expected_count = None
    header_read = False

    try:
        with open(path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue

                #The first non-blank line holds the number of students
                if not header_read:
                    header_read = True
                    try:
                        expected_count = int(line)
                    except ValueError:
                        problems.append(f"Line {line_number}: the first line should be " "the number of students.")
                    continue

                try:
                    student = parseStudent(line)
                except ValueError as error:
                    problems.append(f"Line {line_number}: {error}")
                    continue

                if student.code in codes_seen:
                    problems.append(f"Line {line_number}: duplicate code {student.code}.")
                    continue

                codes_seen.add(student.code)
                students.append(student)
    except FileNotFoundError:
        problems.append(f"Could not find the data file: {path}")
    except (OSError, UnicodeDecodeError) as error:
        problems.append(f"The data file could not be read: {error}")

    #Cross-check the count on the first line against what was loaded
    if expected_count is not None and expected_count != len(students):
        problems.append(f"The file says {expected_count} students but " f"{len(students)} valid records were loaded.")

    return students, problems

class StudentManager:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)

        #Student records
        self.students, problems = loadStudents(DATA_FILE)
        if problems:
            self.reportProblems(problems)

        self.placeholder = tk.Label(self.root, text="Student Manager", font=("Arial", 24, "bold"))
        self.placeholder.pack(pady=200)

    def reportProblems(self, problems):
        shown = problems[:MAX_PROBLEMS_SHOWN]
        message = "\n".join(shown)
        if len(problems) > MAX_PROBLEMS_SHOWN:
            message += f"\n...and {len(problems) - MAX_PROBLEMS_SHOWN} more."
        messagebox.showwarning("Problems with the data file", message)    

def main():
    root = tk.Tk()
    StudentManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()