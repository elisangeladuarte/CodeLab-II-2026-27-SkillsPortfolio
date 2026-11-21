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
#Sort choices: label shown to the user -> function that gives the sort key
SORT_KEYS = {
    "Name": lambda student: student.name.lower(),
    "Student number": lambda student: student.code,
    "Coursework total": lambda student: student.coursework_total,
    "Exam mark": lambda student: student.exam,
    "Overall percentage": lambda student: student.percentage,
}

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

def saveStudents(path, students):
    lines = [str(len(students))]
    for student in students:
        marks = ",".join(str(mark) for mark in student.coursework)
        lines.append(f"{student.code},{student.name},{marks},{student.exam}")

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")
    except OSError as error:
        messagebox.showerror("Save failed", f"The file could not be saved:\n{error}")
        return False
    return True

def buildStudent(code_text, name, mark_texts, exam_text, existing_codes):
    name = name.strip()
    if not name:
        raise ValueError("The name can't be empty.")
    if "," in name:
        raise ValueError("The name can't contain a comma (the file uses commas).")

    try:
        code = int(code_text)
    except ValueError:
        raise ValueError("The student code must be a whole number.") from None
    if not MIN_CODE <= code <= MAX_CODE:
        raise ValueError(f"The student code must be {MIN_CODE}-{MAX_CODE}.")
    if code in existing_codes:
        raise ValueError(f"The code {code} is already in use.")

    try:
        coursework = [int(text) for text in mark_texts]
        exam = int(exam_text)
    except ValueError:
        raise ValueError("All marks must be whole numbers.") from None
    if any(not 0 <= mark <= MAX_COURSEWORK_MARK for mark in coursework):
        raise ValueError(f"Coursework marks must be 0-{MAX_COURSEWORK_MARK}.")
    if not 0 <= exam <= MAX_EXAM_MARK:
        raise ValueError(f"The exam mark must be 0-{MAX_EXAM_MARK}.")

    return Student(code, name, coursework, exam)

def averagePercentage(students):
    if not students:
        return 0.0
    return sum(student.percentage for student in students) / len(students)

def findExtremes(students, highest=True):
    if not students:
        return []

    pick = max if highest else min
    target = pick(student.total for student in students)
    return [student for student in students if student.total == target]

def sortStudents(students, key_name, descending=False):
    return sorted(students, key=SORT_KEYS[key_name], reverse=descending)

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
        #Left column holds the menu, right column holds the results
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        #Menu
        menu_frame = tk.Frame(self.root, padx=15, pady=15)
        menu_frame.grid(row=0, column=0, sticky="ns")

        tk.Label(menu_frame, text="MENU", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        menu_options = [
            ("1. View all student records", self.viewAll),
            ("2. View individual student record", self.viewIndividual),
            ("3. Show highest total score", self.showHighest),
            ("4. Show lowest total score", self.showLowest),
            ("5. Sort student records", self.showSorted),
            ("6. Add a student record", self.addStudent),
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
        
    def showStudents(self, students, summary=None):
        self.clearTable()

        for student in students:
            self.table.insert(
                "",
                "end",
                values=(
                    student.name,
                    student.code,
                    student.coursework_total,
                    student.exam,
                    f"{student.percentage:.1f}%",
                    student.grade,
                ),
            )

        if summary is None:
            summary = (
                f"Students in class: {len(students)}    "
                f"Average percentage: {averagePercentage(students):.1f}%"
            )
        self.summary_label.config(text=summary, fg="black")

    def viewAll(self):
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg="red")
            return
        self.showStudents(self.students)
        
    def chooseStudent(self, title, prompt):
        #Alphabetical order makes a long list easier to scan
        ordered = sorted(self.students, key=lambda student: student.name.lower())
        labels = [f"{student.name} ({student.code})" for student in ordered]
        chosen = None

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root) #Keep it on top of the main window
        dialog.resizable(False, False)

        def confirm():
            """OK button: remember the selection and close the pop-up."""
            nonlocal chosen
            index = combo.current() #-1 if nothing is selected
            if index >= 0:
                chosen = ordered[index]
            dialog.destroy()

        tk.Label(dialog, text=prompt, font=("Arial", 11)).pack(padx=20, pady=(15, 5))

        #State="readonly" stops the user typing something that isn't in the list
        combo = ttk.Combobox(dialog, values=labels, state="readonly", width=35)
        combo.pack(padx=20, pady=5)
        combo.current(0) #Preselect the first student

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=(10, 15))
        tk.Button(button_frame, text="OK", width=10, command=confirm).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)

        dialog.bind("<Return>", lambda event: confirm())
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        #Modal: block the main window until this pop-up is closed
        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

        return chosen 

    def viewIndividual(self):
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg="red")
            return

        student = self.chooseStudent(
            "View individual record", "Select a student:"
        )
        if student is None:
            return #The user cancelled, so leave the display unchanged

        self.showStudents([student], summary=f"Showing the record for {student.name}.")          
        
    def showExtreme(self, highest):
        """Show the student(s) with the highest or lowest total mark.

        Args:
            highest (bool): True for the highest total, False for the lowest.
        """
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg="red")
            return

        matches = findExtremes(self.students, highest)
        word = "highest" if highest else "lowest"
        total = matches[0].total

        if len(matches) == 1:
            summary = f"Student with the {word} total: {total}/{MAX_TOTAL} marks."
        else:
            summary = (
                f"{len(matches)} students tied for the {word} total: "
                f"{total}/{MAX_TOTAL} marks."
            )
        self.showStudents(matches, summary=summary)

    def showHighest(self):
        self.showExtreme(highest=True)

    def showLowest(self):
        self.showExtreme(highest=False)    

    def chooseSortOrder(self):
        result = None

        dialog = tk.Toplevel(self.root)
        dialog.title("Sort student records")
        dialog.transient(self.root)
        dialog.resizable(False, False)

        def confirm():
            """OK button: remember the choices and close the pop-up."""
            nonlocal result
            result = (key_combo.get(), direction.get() == "descending")
            dialog.destroy()

        tk.Label(dialog, text="Sort by:", font=("Arial", 11)).pack(padx=20, pady=(15, 5))
        key_combo = ttk.Combobox(dialog, values=list(SORT_KEYS), state="readonly", width=25)
        key_combo.pack(padx=20, pady=5)
        key_combo.current(0)

        #Radio buttons share one variable, so only one can be selected
        direction = tk.StringVar(value="ascending")
        tk.Radiobutton(dialog, text="Ascending (low to high, A-Z)", variable=direction, value="ascending",).pack(anchor="w", padx=30)
        tk.Radiobutton(dialog, text="Descending (high to low, Z-A)", variable=direction, value="descending",).pack(anchor="w", padx=30)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=(10, 15))
        tk.Button(button_frame, text="OK", width=10, command=confirm).pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", width=10, command=dialog.destroy).pack(side="left", padx=5)

        dialog.bind("<Return>", lambda event: confirm())
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

        return result

    def showSorted(self):
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg="red")
            return

        choice = self.chooseSortOrder()
        if choice is None:
            return #Cancelled, so leave the display unchanged

        key_name, descending = choice
        ordered = sortStudents(self.students, key_name, descending)
        direction = "descending" if descending else "ascending"
        self.showStudents(ordered, summary=f"All {len(ordered)} students sorted by {key_name.lower()} ({direction}).",)    

    def askStudentDetails(self, title, student=None):
        result = None
        #A student keeping their own code must not clash with themselves
        existing_codes = {s.code for s in self.students if s is not student}

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.resizable(False, False)

        labels = [
            "Student name", "Student code (1000-9999)",
            "Coursework mark 1 (/20)", "Coursework mark 2 (/20)",
            "Coursework mark 3 (/20)", "Exam mark (/100)",
        ]
        initial = [""] * len(labels)
        if student is not None:
            initial = [
                student.name, student.code, *student.coursework, student.exam,
            ]

        entries = []
        for row, (label, value) in enumerate(zip(labels, initial)):
            tk.Label(dialog, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(20, 10), pady=4
            )
            entry = tk.Entry(dialog, width=25)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, padx=(0, 20), pady=4)
            entries.append(entry)

        error_label = tk.Label(dialog, text="", fg="red", wraplength=300)
        error_label.grid(row=len(labels), column=0, columnspan=2, pady=(5, 0))

        def confirm():
            """Save button: validate the form and close it if everything is valid."""
            nonlocal result
            name, code, m1, m2, m3, exam = (entry.get().strip() for entry in entries)
            try:
                result = buildStudent(code, name, [m1, m2, m3], exam, existing_codes)
            except ValueError as error:
                error_label.config(text=str(error)) #Stay open so they can fix it
                return
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.grid(row=len(labels) + 1, column=0, columnspan=2, pady=15)
        tk.Button(button_frame, text="Save", width=10, command=confirm).pack(
            side="left", padx=5
        )
        tk.Button(button_frame, text="Cancel", width=10, command=dialog.destroy).pack(
            side="left", padx=5
        )

        dialog.bind("<Return>", lambda event: confirm())
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        entries[0].focus_set()

        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

        return result

    def addStudent(self):
        """Option 6: add a new student and save the file."""
        student = self.askStudentDetails("Add a student record")
        if student is None:
            return #Cancelled

        self.students.append(student)
        if not saveStudents(DATA_FILE, self.students):
            self.students.remove(student) #Keep memory and file in step
            return

        self.showStudents(
            [student],
            summary=f"Added {student.name}. The class now has {len(self.students)} students.",
        )         

def main():
    root = tk.Tk()
    StudentManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()