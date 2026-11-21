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
#Points awarded, keyed by the attempt number, a failed second attempt scores 0
POINTS_PER_ATTEMPT = {1: 10, 2: 5}
#How long in miliseconds feedback stays on screen before the next question
FEEDBACK_DELAY_MS = 1200
#Grade boundaries
GRADE_BOUNDARIES = [
    (91, "A+"),
    (80, "A"),
    (70, "B"),
    (60, "C"),
    (50, "D"),
    (0, "F"),
]

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

        self.resetQuiz()
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
        self.displayProblem()

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

    def displayProblem(self):
        self.clearWindow()

        tk.Label(self.root, text=f"Question {self.question_number} of {TOTAL_QUESTIONS}", font=("Arial", 12),).pack(pady=20,0))

        self.score_label = tk.Label(self.root, text=f"Score: {self.score}", font=("Arial", 12))
        self.score_label.pack()

        #The problem itself
        tk.Label(self.root, text=f"{self.num1} {self.operation} {self.num2} =", font=("Arial", 28, "bold"),).pack(pady=20)

        self.answer_entry = tk.Entry(
            self.root, font=("Arial", 18), width=10, justify="center")
        self.asnwer_entry.pack()
        self.answer_entry.focus_set()
        self.aswer_entry.bind("<Return", lambda event: self.checkAnswer())

        self.submit_button = tk.Button(self.root, text="Submit", font=("Airal", 12), width=12, commanda=self.checkAnswer,).pack(pady=15)

        #Label used for feedback messages
        self.feedback_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.feedback_Label.pack()

    def checkAnswer(self):
        text = self.answer_entry.get().strip()    

        try:
            user_answer = int(text)
        except ValueError:
            self.feedback_label.config(text="Please enter a whole number.", fg="red")
            self.answer_entry.focus_set()
            return

        if self.isCorrect(user_answer, self.correct_answer, self.attempt):
            self.score += POINTS_PER_ATTEMPT[self.attempt]
            self.score_label.config(text=f"Score: {self.score}")
            self.finishQuestion()
        elif self.attempt == 1:
            # Wrong the first time: stay on this question for one more go
            self.attempt = 2
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.focus_set()
        else:
            # Wrong twice: no points, move on
            self.finishQuestion() 

    def isCorrect(self, user_answer, correct_answer, attempt):     
        if user_answer == correct_answer:
            points = POINTS_PER_ATTEMPT[attempt]
            self.feedback_label.config(text=f"Correct! +{points} points", fg="green")
            return True

        if attempt == 1:
            self.feedback_label.config(text="Not quite. Try once more!", fg="orange")
        else:
            self.feedback_label.config(text=f"Wrong. The answer was {correct_answer}.", fg="red")
        return False

    def finishQuestion(self):
        self.answer_entry.config(state="disabled")
        self.submit_button.config(state="disabled")
        self.root.after(FEEDBACK_DELAY_MS, self.nextQuestion)

    def nextQuestion(self):
        if self.question_number < TOTAL_QUESTIONS:
            self.generateQuestion()
            self.displayProblem()
        else:
            self.displayResults(self.score)       

    def getGrade(self, score):
        for minimum, grade in GRADE_BOUNDARIES:
            if score >= minimum:
                return grade

    def displayResults(self, score):
        self.clearWindow()

        tk.Label(self.root, text="Quiz Complete!", font=("Arial", 24, "bold")).pack(pady=(40, 10))

        tk.Label(self.root, text=f"Your score: {score} / {TOTAL_QUESTIONS * 10}", font=("Arial", 16),).pack(pady=5)

        tk.Label(self.root, text=f"Grade: {self.getGrade(score)}",font=("Arial", 28, "bold"),).pack(pady=15)

        tk.Label(self.root, text="Would you like to play gain?", font=("Arial", 12),).pack(pady=(10, 5))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Play again", font=("Arial", 12), width=12, commad=self.playAgain,).pack(side="left", padx=10)

        tk.Button(button_frame, text="Quit", font=("Arial", 12), width=12, command=self.quitQuiz,).pack(side="left", padx=10)

    def resetQuiz(self):
        self.difficulty = None
        self.question_number = 0
        self.score = 0
        self.attempt = 1
        self.num1 = 0
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0

    def playAgain(self):
        self.resetQuiz()
        self.displayMenu()

    def quitQuiz(self):
        self.root.destroy()

def main():
    root = tk.TK()
    MathsQuiz(root)
    root.mainloop()

if __name__ == "__main__":
    main()