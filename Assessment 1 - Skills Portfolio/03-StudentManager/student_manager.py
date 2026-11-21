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
#Table columns: (heading, width in pixels, text alignment)
TABLE_COLUMNS = [
    ("Name", 200, "w"),
    ("Number", 80, "center"),
    ("Coursework (/60)", 120, "center"),
    ("Exam (/100)", 100, "center"),
    ("Percentage", 100, "center"),
    ("Grade", 70, "center"),
]

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

        self.createWidgets()
    
        self.placeholder = tk.Label(self.root, text="Student Manager", font=("Arial", 24, "bold"))
        self.placeholder.pack(pady=200)

    def reportProblems(self, problems):
        shown = problems[:MAX_PROBLEMS_SHOWN]
        message = "\n".join(shown)
        if len(problems) > MAX_PROBLEMS_SHOWN:
            message += f"\n...and {len(problems) - MAX_PROBLEMS_SHOWN} more."
        messagebox.showwarning("Problems with the data file", message)   

    def createWidgets(self):
        # Left column holds the menu, right column holds the results
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        #Menu
        menu_frame = tk.Frame(self.root, padx=15, pady=15)
        menu_frame.grid(row=0, column=0, sticky="ns")

        tk.Label(menu_frame, text="MENU", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        menu_options = [
            ("1. View all student records", self.comingSoon),
            ("2. View individual student record", self.comingSoon),
            ("3. Show highest total score", self.comingSoon),
            ("4. Show lowest total score", self.comingSoon),
        ]
        for text, handler in menu_options:
            tk.Button(menu_frame, text=text, font=("Arial", 10), width=32, anchor="w", command=handler,).pack(pady=3)

        #Results area
        display_frame = tk.Frame(self.root, padx=10, pady=15)
        display_frame.grid(row=0, column=1, sticky="nsew")
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)

        headings = [heading for heading, _, _ in TABLE_COLUMNS]
        self.table = ttk.Treeview(display_frame, columns=headings, show="headings", selectmode="browse")
        for heading, width, alignment in TABLE_COLUMNS:
            self.table.heading(heading, text=heading)
            self.table.column(heading, width=width, anchor=alignment)
        self.table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        #Summary
        self.summary_label = tk.Label(display_frame, text="Choose an option from the menu.", font=("Arial", 11), anchor="w",)
        self.summary_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        #Without any data there is nothing to show
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg="red")

    def clearTable(self):
        self.table.delete(*self.table.get_children())

    def comingSoon(self):
        self.summary_label.config(text="That option isn't built yet.", fg="black")         

def main():
    root = tk.Tk()
    StudentManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()