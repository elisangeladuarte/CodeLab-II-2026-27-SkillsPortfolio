import random
import tkinter as tk
from tkinter import messagebox

#Constants
WINDOW_TITLE = "Maths Quiz"
WINDOW_SIZE = "500x400"
TOTAL_QUESTIONS = 10
#Difficulty levels: number -> label shown on the button
DIFFICULTY_LEVELS = {1: "Easy", 2:"Moderate", 3:"Advanced"}

class MathsQuiz:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        #Quiz state
        self.difficulty = None #1 = easy, 2 = moderate, 3 = advanced
        self.question_number = 0 #Which question the user is on (1-10)
        self.score = 0 #Running total out of 100
        self.attempt = 1 #1 = first attempt, 2 = second attempt
        self.num1 = 0 #Current question values
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0

        self.displayMenu()

    def clearWindow(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def displayMenu(self):
        self.clearWindow()

        tk.Label(self.root, text="Maths Quiz", font=("Arial", 24, "bold")).pack(pady=(30, 10))

        tk.Label(self.root, text="DIFFICULTY LEVEL", font=("Arial", 14)).pack(pady=(0, 20))

    for level, name in DIFFICULTY_LEVELS.items():
        tk.Button(self.root, text=f"{level}. {name}", font=("Arial", 12), width=20, command=lambda level=level: self.selectDifficulty(level)).pack(pady=5)

    def selectDifficulty(self, level):
        self.difficulty = level
        self.question_number = 0
        self.score = 0
        self.attempt = 1

        messagebox.showinfo(
            "Difficulty selected", f"You chose {DIFFICULTY_LEVELS[level]}."
        )    

def main():
    root = tk.TK()
    MathsQuiz(root)
    root.mainloop()

if __name__ == "__main__":
    main()