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

class StudentManager:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)

        #Student records
        self.students = []

        self.placeholder = tk.Label(self.root, text="Student Manager", font=("Arial", 24, "bold"))
        self.placeholder.pack(pady=200)

def main():
    root = tk.Tk()
    StudentManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()