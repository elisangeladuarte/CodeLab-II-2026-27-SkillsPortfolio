import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# Constants
WINDOW_TITLE = "Maths Quiz"
WINDOW_SIZE = "760x620"
TOTAL_QUESTIONS = 10

# Difficulty levels: number -> label shown on the button
DIFFICULTY_LEVELS = {1: "Easy", 2: "Moderate", 3: "Advanced"}

DIFFICULTY_HINTS = {1: "1-digit numbers", 2: "2-digit numbers", 3: "4-digit numbers"}

# Difficulty level -> minimum, maximum value for each number
# Easy = 1 digit (1-9), Moderate = 2 digits (10-99), Advanced = 4 digits (1000-9999)
DIFFICULTY_RANGES = {1: (1, 9), 2: (10, 99), 3: (1000, 9999)}

# Points awarded, keyed by the attempt number, a failed second attempt scores 0
POINTS_PER_ATTEMPT = {1: 10, 2: 5}

# How long in milliseconds feedback stays on screen before the next question
FEEDBACK_DELAY_MS = 1200

# The streak label turns green once the streak reaches this length
STREAK_HIGHLIGHT = 3

# Seconds allowed for each attempt, by difficulty level
TIME_LIMITS = {1: 15, 2: 25, 3: 45}

# The timer turns red when this many seconds (or fewer) are left
WARNING_SECONDS = 5

# Width and height (in pixels) of the small circular timer
RING_SIZE = 64

# Width (in pixels) of the stat tiles on the results screen
TILE_WIDTH = 170

# Leaderboard
LEADERBOARD_FILE = Path(__file__).parent / "leaderboard.json"
MAX_SCORES = 5  # How many scores are kept for each difficulty
MAX_NAME_LENGTH = 12
DEFAULT_NAME = "Player"

# Grade boundaries
GRADE_BOUNDARIES = [
    (91, "A+"),
    (80, "A"),
    (70, "B"),
    (60, "C"),
    (50, "D"),
    (0, "F"),
]

FONT = "Segoe UI"

# Colours
BG = "#0F0D24"  # Window background
CARD = "#1A1740"  # Panels
CARD_HOVER = "#262266"  # A button or row when the mouse is over it
BORDER = "#322E70"  # Thin outlines
ACCENT = "#7C5CFF"  # Main buttons
ACCENT_HOVER = "#9077FF"
ACCENT_SOFT = "#B3A6FF"  # Soft purple for small labels
TEXT = "#F2F0FF"
MUTED = "#9A96BF"
SUCCESS = "#3DDC97"  # Correct
WARN = "#FFB84D"  # Try again
ERROR = "#FF6B7A"  # Wrong


def loadLeaderboard():
    board = {str(level): [] for level in DIFFICULTY_LEVELS}

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return board

    if isinstance(saved, dict):
        for level in board:
            if level in saved:
                board[level] = saved[level]
    return board


def saveLeaderboard(board):
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
            json.dump(board, file, indent=2)
    except OSError:
        return False
    return True


def addScore(board, level, name, score, best_streak):
    entries = board[str(level)]
    entry = {"name": name, "score": score, "streak": best_streak}
    entries.append(entry)

    # Highest score first. The sort is stable, so on a tie the older score stays higher.
    entries.sort(key=lambda item: item["score"], reverse=True)
    del entries[MAX_SCORES:]  # Drop anything below the top few

    for position, item in enumerate(entries, start=1):
        if item is entry:
            return position, entry
    return None, entry


# Drawing helpers
def roundedRectangle(canvas, x1, y1, x2, y2, radius, fill, tag):
    # The radius can't be bigger than half of the width or the height
    radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    diameter = radius * 2

    corners = [
        (x1, y1),
        (x2 - diameter, y1),
        (x1, y2 - diameter),
        (x2 - diameter, y2 - diameter),
    ]
    for x, y in corners:
        canvas.create_oval(
            x, y, x + diameter, y + diameter, fill=fill, outline="", tags=tag
        )

    canvas.create_rectangle(
        x1 + radius, y1, x2 - radius, y2, fill=fill, outline="", tags=tag
    )
    canvas.create_rectangle(
        x1, y1 + radius, x2, y2 - radius, fill=fill, outline="", tags=tag
    )


class RoundedButton(tk.Canvas):

    def __init__(
        self,
        parent,
        text,
        command,
        width=200,
        height=46,
        hint="",
        radius=23,
        fill=ACCENT,
        hover=ACCENT_HOVER,
        text_colour="white",
        background=BG,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=background,
            highlightthickness=0,
            cursor="hand2",
        )
        self.command = command
        self.fill = fill
        self.hover = hover
        self.text_colour = text_colour
        self.enabled = True

        roundedRectangle(self, 0, 0, width, height, radius, fill, "shape")

        if hint:
            # The name sits on the left and the small hint on the right
            self.label = self.create_text(
                22,
                height // 2,
                text=text,
                anchor="w",
                fill=text_colour,
                font=(FONT, 12, "bold"),
            )
            self.hint = self.create_text(
                width - 22,
                height // 2,
                text=hint,
                anchor="e",
                fill=MUTED,
                font=(FONT, 10),
            )
        else:
            self.label = self.create_text(
                width // 2,
                height // 2,
                text=text,
                fill=text_colour,
                font=(FONT, 12, "bold"),
            )
            self.hint = None

        self.bind("<Enter>", lambda event: self.setHover(True))
        self.bind("<Leave>", lambda event: self.setHover(False))
        self.bind("<Button-1>", self.click)

    def setHover(self, inside):

        if not self.enabled:
            return
        self.itemconfig("shape", fill=self.hover if inside else self.fill)
        if self.hint:
            self.itemconfig(self.hint, fill=TEXT if inside else MUTED)

    def click(self, event):

        if self.enabled:
            self.command()

    def setEnabled(self, enabled):

        self.enabled = enabled
        if enabled:
            self.itemconfig("shape", fill=self.fill)
            self.itemconfig(self.label, fill=self.text_colour)
            self.config(cursor="hand2")
        else:
            self.itemconfig("shape", fill=BORDER)
            self.itemconfig(self.label, fill=MUTED)
            self.config(cursor="arrow")


class Card(tk.Canvas):
    """A rounded panel. Put other widgets inside it using its .body frame."""

    def __init__(self, parent, width, height, radius=36, fill=CARD, background=BG):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=background,
            highlightthickness=0,
        )
        roundedRectangle(self, 0, 0, width, height, radius, fill, "shape")

        # The body is a plain square frame, so it must sit far enough from
        # the edge to stay clear of the rounded corners (bigger radius = bigger gap)
        gap = radius // 3 + 2
        self.body = tk.Frame(self, bg=fill)
        self.create_window(
            width // 2,
            height // 2,
            window=self.body,
            width=width - 2 * gap,
            height=height - 2 * gap,
        )


def makeEntry(
    parent, variable, width, background=CARD, size=13, justify="left", height=46
):

    box = Card(
        parent, width=width, height=height, radius=22, fill=BG, background=background
    )
    entry = tk.Entry(
        box.body,
        textvariable=variable,
        font=(FONT, size),
        justify=justify,
        bg=BG,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        highlightthickness=0,
        disabledbackground=BG,
        disabledforeground=MUTED,
    )
    entry.pack(fill="both", expand=True, padx=12)
    return box, entry


class MathsQuiz:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.setupStyle()

        self.name_var = tk.StringVar()  # Holds the name box text between screens
        self.leaderboard = loadLeaderboard()

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
        self.player_name = ""

    def resetQuiz(self):
        self.difficulty = None  # 1 = easy, 2 = moderate, 3 = advanced
        self.question_number = 0  # Which question the user is on (1-10)
        self.score = 0  # Running total out of 100
        self.streak = 0  # Correct first attempt in a row
        self.best_streak = 0  # Longest streak this quiz
        self.attempt = 1  # 1 = first attempt, 2 = second attempt
        self.num1 = 0  # Current question values
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0
        self.time_left = 0  # Seconds left for the current attempt
        self.timer_job = None  # The pending root.after call, so we can cancel it
        self.history = []
        self.current_answers = []
        self.player_name = DEFAULT_NAME
        self.rank = None  # Leaderboard position of the latest result
        self.last_entry = None  # The latest result, so its row can be highlighted
        self.saved_ok = True

    def clearWindow(self):
        self.cancelTimer()
        for widget in self.root.winfo_children():
            widget.destroy()

    def displayMenu(self):
        self.clearWindow()
        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Maths Quiz", font=(FONT, 32, "bold")).pack()
        tk.Label(
            page,
            text="10 questions  \u00b7  2 attempts each  \u00b7  beat the clock",
            font=(FONT, 11),
            fg=MUTED,
        ).pack(pady=(4, 22))

        # Everything else sits inside one rounded card
        card = Card(page, width=460, height=330)
        card.pack()
        body = card.body

        tk.Label(
            body, text="YOUR NAME", font=(FONT, 9, "bold"), fg=MUTED, bg=CARD
        ).pack(anchor="w", padx=20, pady=(20, 6))
        name_box, _ = makeEntry(body, self.name_var, width=384)
        name_box.pack(padx=20)

        tk.Label(
            body, text="DIFFICULTY LEVEL", font=(FONT, 9, "bold"), fg=MUTED, bg=CARD
        ).pack(anchor="w", padx=20, pady=(18, 6))

        # level=level captures the current value for each button
        for level, name in DIFFICULTY_LEVELS.items():
            RoundedButton(
                body,
                f"{level}.  {name}",
                lambda level=level: self.selectDifficulty(level),
                width=384,
                height=44,
                hint=DIFFICULTY_HINTS[level],
                fill=BG,
                hover=ACCENT,
                # outline=BORDER,
                # hover_outline=ACCENT,
                text_colour=TEXT,
                background=CARD,
            ).pack(padx=20, pady=3)

        RoundedButton(
            page,
            "View leaderboard",
            lambda: self.displayLeaderboard(1, self.displayMenu),
            width=200,
            height=40,
            fill=BG,
            hover=CARD_HOVER,
            # outline=BG,
            # hover_outline=BORDER,
            text_colour=MUTED,
        ).pack(pady=(18, 0))

    def selectDifficulty(self, level):
        name = self.name_var.get().strip()[:MAX_NAME_LENGTH] or DEFAULT_NAME

        self.resetQuiz()
        self.difficulty = level
        self.generateQuestion()
        self.displayProblem()

    # Question generation
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

    # Question screen
    def displayProblem(self):

        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        card = Card(page, width=520, height=440)
        card.pack()
        body = card.body

        # Top row: question number on the left, small timer ring on the right
        header = tk.Frame(body, bg=CARD)
        header.pack(fill="x", padx=28, pady=(20, 0))

        tk.Label(
            header,
            text=f"Question {self.question_number} of {TOTAL_QUESTIONS}",
            font=(FONT, 11),
            fg=MUTED,
            bg=CARD,
        ).pack(side="left")

        self.timer_canvas = tk.Canvas(
            header,
            width=RING_SIZE,
            height=RING_SIZE,
            bg=CARD,
            highlightthickness=0,
        )
        self.timer_canvas.pack(side="right")

        self.attempt_label = tk.Label(body, text="", font=(FONT, 10, "bold"), bg=CARD)
        self.attempt_label.pack()

        tk.Label(
            body,
            text=f"{self.num1} {self.operation} {self.num2} =",
            font=(FONT, 52, "bold"),
            bg=CARD,
        ).pack(pady=(6, 20))

        box, self.answer_entry = makeEntry(
            body, None, width=240, size=22, justify="center", height=58
        )
        box.pack()
        self.answer_entry.focus_set()
        self.answer_entry.bind("<Return>", lambda event: self.checkAnswer())

        self.feedback_label = tk.Label(body, text="", font=(FONT, 12), bg=CARD)
        self.feedback_label.pack(pady=(14, 10))

        self.submit_button = RoundedButton(
            body,
            "Submit",
            self.checkAnswer,
            width=180,
            height=46,
            background=CARD,
        )
        self.submit_button.pack()

        # Small stat chips under the card
        chips = tk.Frame(page)
        chips.pack(pady=(16, 0))
        self.streak_label = self.makeChip(chips, "Streak", 120)
        self.score_label = self.makeChip(chips, "Score", 120)
        self.best_label = self.makeChip(chips, "Best streak", 150)

        self.updateAttemptLabel()
        self.updateStats()
        self.startTimer()

    def makeChip(self, parent, caption, width):

        chip = Card(parent, width=width, height=40, radius=20)
        chip.pack(side="left", padx=6)

        inner = tk.Frame(chip.body, bg=CARD)
        inner.pack(expand=True)
        tk.Label(inner, text=caption, font=(FONT, 10), fg=MUTED, bg=CARD).pack(
            side="left", padx=(0, 6)
        )
        value = tk.Label(inner, text="0", font=(FONT, 11, "bold"), bg=CARD)
        value.pack(side="left")
        return value

    def makeTile(self, parent, caption, pady=0, side="top", padx=0):

        tile = Card(parent, width=TILE_WIDTH, height=108, radius=26)
        tile.pack(pady=pady, side=side, padx=padx)
        tk.Label(
            tile.body, text=caption, font=(FONT, 9, "bold"), fg=MUTED, bg=CARD
        ).pack(pady=(8, 0))
        number = tk.Label(tile.body, text="0", font=(FONT, 24, "bold"), bg=CARD)
        number.pack()
        note = tk.Label(tile.body, text="", font=(FONT, 9), fg=MUTED, bg=CARD)
        note.pack()
        return number, note

    def updateAttemptLabel(self):

        if self.attempt == 1:
            self.attempt_label.config(text="FIRST ATTEMPT", fg=ACCENT_SOFT)
        else:
            self.attempt_label.config(text="LAST CHANCE", fg=WARN)

    def updateStats(self):

        self.score_label.config(text=str(self.score))

        colour = SUCCESS if self.streak >= STREAK_HIGHLIGHT else TEXT
        self.streak_label.config(text=str(self.streak), fg=colour)
        self.best_label.config(text=str(self.best_streak))

    # Timer
    def startTimer(self):
        self.cancelTimer()
        self.time_left = TIME_LIMITS[self.difficulty]
        self.drawTimer()
        self.timer_job = self.root.after(1000, self.tick)

    def tick(self):
        self.time_left -= 1
        self.drawTimer()

        if self.time_left <= 0:
            self.timeUp()
        else:
            self.timer_job = self.root.after(1000, self.tick)

    def cancelTimer(self):
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def drawTimer(self):

        canvas = self.timer_canvas
        canvas.delete("all")

        edge = 5
        size = RING_SIZE
        fraction = max(self.time_left, 0) / TIME_LIMITS[self.difficulty]
        colour = ERROR if self.time_left <= WARNING_SECONDS else ACCENT

        # The grey track (a full circle)
        canvas.create_oval(edge, edge, size - edge, size - edge,
                           outline=BORDER, width=5)

        # The coloured arc starts at the top and shrinks as time runs out.
        # (359.9 instead of 360 because a full 360 degree arc doesn't draw.)
        if fraction > 0:
            canvas.create_arc(
                edge, edge, size - edge, size - edge, style="arc", start=90,
                extent=-359.9 * fraction, outline=colour, width=5,
            )

        canvas.create_text(size // 2, size // 2, text=str(max(self.time_left, 0)),
                           fill=TEXT, font=(FONT, 14, "bold"))

    def timeUp(self):
        self.timer_job = None
        self.current_answers.append(None)

        if self.attempt == 1:
            self.feedback_label.config(text="Time's up! Try once more!", fg=WARN)
        else:
            self.feedback_label.config(
                text=f"Time's up! The answer was {self.correct_answer}.", fg=ERROR
            )
        self.handleMiss()

    # Checking answers
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
            self.feedback_label.config(
                text=f"Wrong. The answer was {correct_answer}.", fg=ERROR
            )
        return False

    def handleMiss(self):
        if self.attempt == 1:
            # A first-attempt miss ends the streak and gives a second go
            self.streak = 0
            self.attempt = 2
            self.updateStats()
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.focus_set()
            self.updateAttemptLabel()
            self.startTimer()
        else:
            self.recordQuestion(0)
            self.finishQuestion()

    def recordQuestion(self, points):
        self.history.append(
            {
                "question": f"{self.num1} {self.operation} {self.num2} =",
                "answers": list(self.current_answers),  # A copy of the list
                "correct": self.correct_answer,
                "points": points,
            }
        )

    def finishQuestion(self):
        self.answer_entry.config(state="disabled")
        self.submit_button.setEnabled(False)
        self.root.after(FEEDBACK_DELAY_MS, self.nextQuestion)

    def nextQuestion(self):
        self.cancelTimer()
        if self.question_number < TOTAL_QUESTIONS:
            self.generateQuestion()
            self.displayProblem()
        else:
            self.finishQuiz()

    def finishQuiz(self):
        self.rank, self.last_entry = addScore(
            self.leaderboard,
            self.difficulty,
            self.player_name,
            self.score,
            self.best_streak,
        )
        self.saved_ok = saveLeaderboard(self.leaderboard)
        self.displayResults(self.score)

    # Results
    def getGrade(self, score):
        for minimum, grade in GRADE_BOUNDARIES:
            if score >= minimum:
                return grade

    def displayResults(self, score):
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Quiz Complete!", font=(FONT, 30, "bold")).pack()
        level_name = DIFFICULTY_LEVELS[self.difficulty]
        tk.Label(
            page,
            text=f"{self.player_name} \u00b7 {level_name}",
            font=(FONT, 11),
            fg=MUTED,
        ).pack(pady=(4, 18))

        # A rounded banner that says how the score did on the leaderboard
        if self.rank == 1:
            message, colour = "New high score!", WARN
        elif self.rank is not None:
            message = f"You placed #{self.rank} on the {level_name} leaderboard."
            colour = TEXT
        else:
            message, colour = "Not on the leaderboard this time.", MUTED

        if not self.saved_ok:
            message += " (The leaderboard file couldn't be saved.)"

        banner = Card(page, width=560, height=40, radius=18)
        banner.pack(pady=(0, 18))
        tk.Label(banner.body, text=message, font=(FONT, 11), fg=colour, bg=CARD).pack(
            expand=True
        )

        # Three tiles side by side
        tiles = tk.Frame(page)
        tiles.pack(pady=(0, 22))

        number, note = self.makeTile(tiles, "FINAL SCORE", side="left", padx=8)
        number.config(text=str(score))
        note.config(text=f"out of {TOTAL_QUESTIONS * 10}")

        number, note = self.makeTile(tiles, "BEST STREAK", side="left", padx=8)
        number.config(text=str(self.best_streak))
        note.config(text="first tries in a row")

        number, note = self.makeTile(tiles, "GRADE", side="left", padx=8)
        number.config(text=self.getGrade(score), fg=ACCENT_SOFT)

        # Buttons sit side by side inside a frame
        buttons = tk.Frame(page)
        buttons.pack()

        RoundedButton(buttons, "Review answers", self.displayReview, width=150).pack(
            side="left", padx=6
        )

        # Dark buttons use the same options, so keep them in one dictionary
        quiet = dict(
            width=150,
            fill=CARD,
            hover=CARD_HOVER,
            #outline=BORDER,
            #hover_outline=ACCENT,
            text_colour=TEXT,
        )
        RoundedButton(
            buttons,
            "Leaderboard",
            lambda: self.displayLeaderboard(
                self.difficulty, lambda: self.displayResults(self.score)
            ),
            **quiet,
        ).pack(side="left", padx=6)
        RoundedButton(buttons, "Play again", self.playAgain, **quiet).pack(
            side="left", padx=6
        )
        RoundedButton(buttons, "Quit", self.quitQuiz, **quiet).pack(side="left", padx=6)

    def displayReview(self):
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Review your answers", font=(FONT, 24, "bold")).pack(
            pady=(0, 10)
        )

        # Column widths (in pixels) shared by the heading row and every row
        widths = [50, 190, 170, 100, 90]

        # Heading row
        heading_row = tk.Frame(page)
        heading_row.pack(padx=(0, 24))  # Lines the headings up with the row text
        for column, heading in enumerate(
            ["", "QUESTION", "YOUR ANSWER", "CORRECT", "POINTS"]
        ):
            heading_row.columnconfigure(column, minsize=widths[column])
            tk.Label(
                heading_row,
                text=heading,
                font=(FONT, 9, "bold"),
                fg=MUTED,
                anchor="w",
            ).grid(row=0, column=column, sticky="w")

        # One rounded row per question
        for record in self.history:
            points = record["points"]
            if points == POINTS_PER_ATTEMPT[1]:
                points_colour, icon = SUCCESS, "\u2713"
            elif points > 0:
                points_colour, icon = WARN, "\u2713"  # Right, but on the second try
            else:
                points_colour, icon = ERROR, "\u2717"

            # "4, 3" means the first answer was 4 and the second was 3
            given = ", ".join(
                "-" if answer is None else str(answer) for answer in record["answers"]
            )

            row = Card(page, width=640, height=36, radius=16)
            row.pack(pady=2)

            values = [icon, record["question"], given, record["correct"], points]
            for column, value in enumerate(values):
                row.body.columnconfigure(column, minsize=widths[column])
                colour = points_colour if column in (0, 4) else TEXT
                tk.Label(
                    row.body,
                    text=value,
                    font=(FONT, 11),
                    fg=colour,
                    bg=CARD,
                    anchor="w",
                ).grid(row=0, column=column, sticky="w")

        RoundedButton(
            page,
            "Back to results",
            lambda: self.displayResults(self.score),
            width=200,
            height=42,
        ).pack(pady=(14, 0))

    def displayLeaderboard(self, level, back):
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Leaderboard", font=(FONT, 30, "bold")).pack(pady=(0, 14))

        # One tab per difficulty. The one being shown is filled with purple.
        tabs = tk.Frame(page)
        tabs.pack(pady=(0, 16))
        for tab_level, name in DIFFICULTY_LEVELS.items():
            chosen = tab_level == level
            RoundedButton(
                tabs,
                name,
                lambda tab_level=tab_level: self.displayLeaderboard(tab_level, back),
                width=120,
                height=38,
                fill=ACCENT if chosen else CARD,
                #outline=ACCENT if chosen else BORDER,
                hover=ACCENT_HOVER if chosen else CARD_HOVER,
                #hover_outline=ACCENT,
                text_colour="white" if chosen else MUTED,
            ).pack(side="left", padx=4)

        # Column widths (in pixels) shared by the heading row and every row
        widths = [60, 220, 100, 110]

        entries = self.leaderboard[str(level)]
        if not entries:
            tk.Label(
                page, text="No scores yet. Be the first!", fg=MUTED, font=(FONT, 12)
            ).pack(pady=40)
        else:
            heading_row = tk.Frame(page)
            heading_row.pack(padx=(0, 34))  # lines the headings up with the row text
            for column, heading in enumerate(["#", "PLAYER", "SCORE", "BEST STREAK"]):
                heading_row.columnconfigure(column, minsize=widths[column])
                tk.Label(
                    heading_row,
                    text=heading,
                    font=(FONT, 9, "bold"),
                    fg=MUTED,
                    anchor="w",
                ).grid(row=0, column=column, sticky="w")

            for position, entry in enumerate(entries, start=1):
                # The row that was just added gets a purple highlight
                latest = entry is self.last_entry
                row_colour = ACCENT if latest else CARD
                row = Card(
                    page,
                    width=540,
                    height=40,
                    radius=20,
                    fill=row_colour,
                    #outline=ACCENT if latest else BORDER,
                )
                row.pack(pady=3)

                values = [position, entry["name"], entry["score"], entry["streak"]]
                for column, value in enumerate(values):
                    row.body.columnconfigure(column, minsize=widths[column])
                    colour = WARN if position == 1 and column == 0 else TEXT
                    tk.Label(
                        row.body,
                        text=value,
                        font=(FONT, 12),
                        fg=colour,
                        bg=CARD_HOVER if latest else CARD,
                        anchor="w",
                    ).grid(row=0, column=column, sticky="w")

        RoundedButton(page, "Back", back, width=160, height=42).pack(pady=(18, 0))

    # Replay and quit
    def playAgain(self):
        self.resetQuiz()
        self.displayMenu()

    def quitQuiz(self):
        self.cancelTimer()
        self.root.destroy()


def main():
    root = tk.Tk()
    MathsQuiz(root)
    root.mainloop()


if __name__ == "__main__":
    main()
