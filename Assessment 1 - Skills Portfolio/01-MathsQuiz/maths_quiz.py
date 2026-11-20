import random
import tkinter as tk
from tkinter import messagebox

#Constants
WINDOW_TITLE = "Maths Quiz"
WINDOW_SIZE = "500x400"
TOTAL_QUESTIONS = 10

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

        self.placeholder = tk.Label(
            self.root, text="Maths Quiz", font=("Arial", 24, "bold")
        )
        self.placeholder.pack(pady=100)

def main():
    root = tk.TK()
    MathsQuiz(root)
    root.mainloop()

if __name__ == "__main__":
    main()