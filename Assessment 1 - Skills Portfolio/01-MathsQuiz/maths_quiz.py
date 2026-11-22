import random
import tkinter as tk
from tkinter import ttk

#Constants
WINDOW_TITLE = "Maths Quiz"
WINDOW_SIZE = "600x520"
TOTAL_QUESTIONS = 10
#Difficulty levels: number -> label shown on the button
DIFFICULTY_LEVELS = {1: "Easy", 2:"Moderate", 3:"Advanced"}
#Difficulty level -> minimum, maximum value for each number
#Easy = 1 digit (1-9), Moderate = 2 digits (10-99), Advanced = 4 digits (1000-9999)
DIFFICULTY_RANGES = {1: (1, 9), 2: (10, 99), 3: (1000, 9999)}
#Points awarded, keyed by the attempt number, a failed second attempt scores 0
POINTS_PER_ATTEMPT = {1: 10, 2: 5}
#How long in milliseconds feedback stays on screen before the next question
FEEDBACK_DELAY_MS = 1200
#The streak label turns green once the streak reaches this length
STREAK_HIGHLIGHT = 3
#Seconds allowed for each attempt, by difficulty level
TIME_LIMITS = {1: 15, 2: 25, 3: 45}
#The timer turns red when this many seconds (or fewer) are left
WARNING_SECONDS = 5
#Grade boundaries
GRADE_BOUNDARIES = [
    (91, "A+"),
    (80, "A"),
    (70, "B"),
    (60, "C"),
    (50, "D"),
    (0, "F"),
]

#Colours
BG = "#14122B"        
CARD = "#1E1B3A"     
ACCENT = "#7C5CFF"   
ACCENT_HOVER = "#9077FF"
TEXT = "#F2F0FF"
MUTED = "#9A96BF"
SUCCESS = "#3DDC97"
WARN = "#FFB84D"      
ERROR = "#FF6B7A"     

class MathsQuiz:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        self.timer_job = None

        self.setupStyle()
        self.resetQuiz()
        self.displayMenu()

    def setupStyle(self):
        self.root.configure(bg=BG)

        self.root.option_add("*Label.background", BG)
        self.root.option_add("*Label.foreground", TEXT)
        self.root.option_add("*Frame.background", BG)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TButton",
            background=ACCENT,
            foreground="white",
            font=("Arial", 12),
            padding=8,
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", ACCENT_HOVER), ("disabled", CARD)],
            foreground=[("disabled", MUTED)],
        )    

    def resetQuiz(self):
        self.difficulty = None #1 = easy, 2 = moderate, 3 = advanced
        self.question_number = 0 #Which question the user is on (1-10)
        self.score = 0 #Running total out of 100
        self.streak = 0 #Correct first attempt in a row
        self.best_streak = 0 #Longest streak this quiz 
        self.attempt = 1 #1 = first attempt, 2 = second attempt
        self.num1 = 0 #Current question values
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0
        self.time_left = 0 #Seconds left for the current attempt
        self.timer_job = None #The pending root.after call, so we can cancel it
        self.history = []
        self.current_answers = []

    def clearWindow(self):
        self.cancelTimer()
        for widget in self.root.winfo_children():
            widget.destroy()

    def displayMenu(self):
        self.clearWindow()

        tk.Label(self.root, text="Maths Quiz", font=("Arial", 24, "bold")).pack(pady=(30, 10))

        tk.Label(self.root, text="DIFFICULTY LEVEL", font=("Arial", 14)).pack(pady=(0, 20))

        for level, name in DIFFICULTY_LEVELS.items():
            ttk.Button(self.root, text=f"{level}. {name}", width=20, command=lambda level=level: self.selectDifficulty(level)).pack(pady=5)

    def selectDifficulty(self, level):
        self.resetQuiz()
        self.difficulty = level
        self.generateQuestion()
        self.displayProblem() 

    def randomInt(self, difficulty):
        minimum, maximum = DIFFICULTY_RANGES[difficulty]
        return random.randint(minimum, maximum)

    def decideOperation(self):
        return random.choice(["+", "-"])

    def generateQuestion(self):
        self.question_number += 1
        self.attempt = 1
        self.current_answers = []
        self.num1 = self.randomInt(self.difficulty)
        self.num2 = self.randomInt(self.difficulty)
        self.operation = self.decideOperation()

        if self.operation == "+":
            self.correct_answer = self.num1 + self.num2
        else:
            self.correct_answer = self.num1 - self.num2    

    #Question screen
    def displayProblem(self):
        self.clearWindow()

        tk.Label(self.root, text=f"Question {self.question_number} of {TOTAL_QUESTIONS}", font=("Arial", 12)).pack(pady=(20, 0))

        stats_frame = tk.Frame(self.root)
        stats_frame.pack()

        self.score_label = tk.Label(stats_frame, text=f"Score: {self.score}", font=("Arial", 12))
        self.score_label.pack(side="left", padx=10)

        self.streak_label = tk.Label(stats_frame, text=f"Streak: {self.streak}", font=("Arial", 12), fg=MUTED,)
        self.streak_label.pack(side="left", padx=10)

        self.timer_label = tk.Label(self.root, text="", font=("Arial, 12"))
        self.timer_label.pack(pady=(5, 0))

        tk.Label(self.root, text=f"{self.num1} {self.operation} {self.num2} =", font=("Arial", 28, "bold"),).pack(pady=20)

        self.answer_entry = tk.Entry(self.root, font=("Arial", 18), width=10, justify="center", bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", disabledbackground=CARD, disabledforeground=MUTED,)
        self.answer_entry.pack()
        self.answer_entry.focus_set()
        self.answer_entry.bind("<Return>", lambda event: self.checkAnswer())

        self.submit_button = ttk.Button(self.root, text="Submit", width=12, command=self.checkAnswer)
        self.submit_button.pack(pady=15)

        self.feedback_label = tk.Label(self.root, text="")
        self.feedback_label.pack()

        self.startTimer()

    def checkAnswer(self):

        if str(self.answer_entry.cget("state")) == "disabled":
            return
        
        text = self.answer_entry.get().strip()    

        try:
            user_answer = int(text)
        except ValueError:
            self.feedback_label.config(text="Please enter a whole number.", fg=ERROR)
            self.answer_entry.focus_set()
            return

        self.current_answers.append(user_answer)

        if self.isCorrect(user_answer, self.correct_answer, self.attempt):
            self.score += POINTS_PER_ATTEMPT[self.attempt]

            if self.attempt == 1:
                self.streak += 1
                self.best_streak = max(self.best_streak, self.streak)

            self.updateStats()
            self.recordQuestion(POINTS_PER_ATTEMPT[self.attempt])
            self.finishQuestion()
        else:
            self.handleMiss() 

    def isCorrect(self, user_answer, correct_answer, attempt):     
        if user_answer == correct_answer:
            points = POINTS_PER_ATTEMPT[attempt]
            self.feedback_label.config(text=f"Correct! +{points} points", fg=SUCCESS)
            return True

        if attempt == 1:
            self.feedback_label.config(text="Not quite. Try once more!", fg=WARN)
        else:
            self.feedback_label.config(text=f"Wrong. The answer was {correct_answer}.", fg=ERROR)
        return False

    def finishQuestion(self):
        self.answer_entry.config(state="disabled")
        self.submit_button.config(state="disabled")
        self.root.after(FEEDBACK_DELAY_MS, self.nextQuestion)

    def nextQuestion(self):
        self.cancelTimer()
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

        tk.Label(self.root, text=f"Best streak: {self.best_streak}", font=("Arial", 12), fg=MUTED,).pack()

        tk.Label(self.root, text=f"Grade: {self.getGrade(score)}",font=("Arial", 28, "bold"),).pack(pady=15)

        tk.Label(self.root, text="Would you like to play gain?", font=("Arial", 12),).pack(pady=(10, 5))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Review answers", command=self.displayReview).pack(side="left", padx=10)

        ttk.Button(button_frame, text="Play again", width=12, commad=self.playAgain,).pack(side="left", padx=10)

        ttk.Button(button_frame, text="Quit", font=("Arial", 12), width=12, command=self.quitQuiz,).pack(side="left", padx=10)

    def resetQuiz(self):
        self.difficulty = None
        self.question_number = 0
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.attempt = 1
        self.num1 = 0
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0
        self.history = []

    def playAgain(self):
        self.resetQuiz()
        self.displayMenu()

    def quitQuiz(self):
        self.cancelTimer()
        self.root.destroy()

    def confirmExit(self):
        if self.question_number == 0 or messagebox.askyesno("Quit", "Leave the quiz? Your progress will be lost."):
            self.root.destroy()

    def updateStats(self):
        self.score_label.config(text=f"Score: {self.score}")

        colour = SUCCESS if self.streak >= STREAK_HIGHLIGHT else MUTED
        self.streak_label.config(text=f"Streak: {self.streak}", fg=colour)  

    def startTimer(self):
        self.cancelTimer()
        self.time_left = TIME_LIMITS[self.difficulty]
        self.updateTimerLabel()
        self.timer_job = self.root.after(1000, self.tick)

    def tick(self):
        self.time_left -= 1
        self.updateTimerLabel()

        if self.time_left <= 0:
            self.timeUp()
        else:
            self.timer_job = self.root.after(1000, self.tick)

    def cancelTimer(self):
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def updateTimerLabel(self):
        colour = ERROR if self.time_left <= WARNING_SECONDS else MUTED
        self.timer_label.config(text=f"Time left: {self.time_left}s", fg=colour)

    def timeUp(self):
        self.timer_job = None
        self.current_answers.append(None)

        if self.attempt == 1:
            self.feedback_label.config(text="Time's up! Try once more!", fg=WARN)
        else:
            self.feedback_label.config(text=f"Time's up! The answer was {self.correct_answer}.", fg=ERROR)
        self.handleMiss()  

    def handleMiss(self):
        if self.attempt == 1:
            #A first-attempt miss ends the streak and gives a second go
            self.streak = 0
            self.attempt = 2
            self.updateStats()
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.focus_set()
            self.startTimer()
        else:
            self.recordQuestion(0)
            self.finishQuestion() 

    def recordQuestion(self, points):
        self.history.append({
            "question": f"{self.num1} {self.operation} {self.num2} =",
            "answers": list(self.current_answers),   #A copy of the list
            "correct": self.correct_answer,
            "points": points,
        })   

    def displayReview(self):
        self.clearWindow()

        tk.Label(self.root, text="Review your answers", font=("Arial", 20, "bold")).pack(pady=(20, 10))

        table = tk.Frame(self.root)
        table.pack()

        #Heading row
        headings = ["#", "Question", "Your answer", "Correct", "Points"]
        for column, heading in enumerate(headings):
            tk.Label(
                table, text=heading, font=("Arial", 11, "bold"), fg=MUTED
            ).grid(row=0, column=column, padx=12, pady=4)

        #One row per question
        for row, record in enumerate(self.history, start=1):
            points = record["points"]
            if points == POINTS_PER_ATTEMPT[1]:
                points_colour = SUCCESS
            elif points > 0:
                points_colour = WARN
            else:
                points_colour = ERROR

            #"4, 3" means the first answer was 4 and the second was 3
            given = ", ".join(
                "-" if answer is None else str(answer)
                for answer in record["answers"]
            )

            values = [row, record["question"], given, record["correct"], points]
            for column, value in enumerate(values):
                colour = points_colour if column == 4 else TEXT
                tk.Label(
                    table, text=value, font=("Arial", 11), fg=colour
                ).grid(row=row, column=column, padx=12, pady=2)

        ttk.Button(
            self.root,
            text="Back to results",
            command=lambda: self.displayResults(self.score),
        ).pack(pady=15)                            

def main():
    root = tk.Tk()
    MathsQuiz(root)
    root.mainloop()

if __name__ == "__main__":
    main()