import random
import tkinter as tk
from tkinter import messagebox

#Constants
WINDOW_TITLE = "Maths Quiz"
WINDOW_SIZE = "500x400"
TOTAL_QUESTIONS = 10
#Difficulty levels: number -> label shown on the button
DIFFICULTY_LEVELS = {1: "Easy", 2:"Moderate", 3:"Advanced"}
#Difficluty level -> minimum, maximum value for each number
#Easy = 1 digit (1-9), Moderate = 2 digits (10-99), Advanced = 4 digits (1000-9999)
DIFFICULTY_RANGES = {1: (1, 9), 2: (10, 99), 3: (1000,9999)}

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

        self.generateQuestion()

        messagebox.showinfo("Test question", f"Question {self.question_number}: " f"{self.num1} {self.operation} {self.num2} = ?\n" f"(Answer: {self.correct_answer})",)  

    def randomIn(self, difficulty):
        minimum, maximum = DIFFICULTY_RANGES[difficulty]
        return random.randint(minimum, maximum)

    def decideOperation(self):
        return random.choice(["+", "-"])

    def generateQuestion(self):
        self.question_number += 1
        self.attempt = 1
        self.num1 = self.randomInt(self.difficulty)
        self.num2 = self.randomInt(self.difficulty)
        self.operation = self.decideOperation()     

def main():
    root = tk.TK()
    MathsQuiz(root)
    root.mainloop()

if __name__ == "__main__":
    main()