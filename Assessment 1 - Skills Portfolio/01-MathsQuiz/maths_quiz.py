# AI acknowledgement: this program was developed with help from Claude
# Prompts used:
# "Redesign the quiz so it looks modern, with a maths theme"
# "Add sound effects and a sound on/off button"

import json
import random
import subprocess
import sys
import tkinter as tk
from pathlib import Path

WINDOW_TITLE = "Maths Quiz"
WINDOW_SIZE = "760x620"
TOTAL_QUESTIONS = 10

DIFFICULTY_LEVELS = {1: "Easy", 2: "Moderate", 3: "Advanced"}

DIFFICULTY_HINTS = {1: "1-digit numbers", 2: "2-digit numbers", 3: "4-digit numbers"}

# Smallest and largest number used at each level
DIFFICULTY_RANGES = {1: (1, 9), 2: (10, 99), 3: (1000, 9999)}

# Points for a correct answer, by attempt number
POINTS_PER_ATTEMPT = {1: 10, 2: 5}

FEEDBACK_DELAY_MS = 1200  # how long feedback stays up before the next question

STREAK_HIGHLIGHT = 3  # streak length at which the number turns green

# Seconds allowed for each attempt, by level
TIME_LIMITS = {1: 15, 2: 25, 3: 45}

WARNING_SECONDS = 5  # the timer turns red at this many seconds left

QUESTION_WIDTH = 520  # width of the quiz screen content, in pixels

# Font size of the question, by level (4-digit numbers need a smaller size to fit)
QUESTION_SIZES = {1: 56, 2: 56, 3: 44}

LEADERBOARD_FILE = Path(__file__).parent / "leaderboard.json"
SOUNDS_DIR = Path(__file__).parent / "sounds"
sound_on = True
MAX_SCORES = 5  # scores kept for each level
MAX_NAME_LENGTH = 12
DEFAULT_NAME = "Player"

# (minimum score, grade), highest first
GRADE_BOUNDARIES = [
    (91, "A+"),
    (80, "A"),
    (70, "B"),
    (60, "C"),
    (50, "D"),
    (0, "F"),
]

# Colours and fonts
FONT = "Segoe UI"
FONT_LIGHT = "Segoe UI Light"
BG = "#0F0D24"
CARD = "#1A1740"
CARD_HOVER = "#262266"
BORDER = "#322E70"  # disabled buttons
ACCENT = "#7C5CFF"
ACCENT_HOVER = "#9077FF"
ACCENT_SOFT = "#B3A6FF"
TEXT = "#F2F0FF"
MUTED = "#9A96BF"
SUCCESS = "#3DDC97"  # correct
WARN = "#FFB84D"  # second chance
ERROR = "#FF6B7A"  # wrong
SYMBOL = "#1C1944"  # faint maths symbols in the background

# (symbol, x, y, font size, tilt in degrees), placed around the edges of the window
SYMBOLS = [
    ("\u03c0", 60, 100, 50, 10),
    ("\u2211", 65, 250, 44, -8),
    ("\u221a", 55, 400, 52, 6),
    ("\u00f7", 60, 540, 40, 0),
    ("%", 150, 330, 40, -4),
    ("\u00d7", 705, 95, 44, -10),
    ("+", 700, 250, 54, 0),
    ("=", 705, 395, 46, 8),
    ("\u221e", 695, 540, 52, -6),
]


def roundedRectangle(canvas, x1, y1, x2, y2, radius, fill, tag):
    """Draw a filled rounded rectangle from four circles and two rectangles.

    Every piece gets the same tag, so canvas.itemconfig(tag, fill=...)
    recolours the whole shape.
    """
    # the radius can't be more than half of either side
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
    """A clickable pill-shaped button drawn on a canvas."""

    def __init__(
        self,
        parent,
        text,
        command,
        width=200,
        height=46,
        hint="",
        radius=30,
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
        """Change colour while the mouse is over the button."""
        if not self.enabled:
            return
        self.itemconfig("shape", fill=self.hover if inside else self.fill)
        if self.hint:
            self.itemconfig(self.hint, fill=TEXT if inside else MUTED)

    def click(self, event):
        """Run the command unless the button is disabled."""
        if self.enabled:
            self.command()

    def setEnabled(self, enabled):
        """Enable the button, or grey it out."""
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
        # a 2 pixel ring in the background colour, recoloured when the box has focus
        roundedRectangle(self, 0, 0, width, height, radius, background, "ring")
        roundedRectangle(self, 2, 2, width - 2, height - 2, radius - 2, fill, "shape")

        # the body frame is square, so keep it clear of the rounded corners
        gap = radius // 3 + 2
        self.body = tk.Frame(self, bg=fill)
        self.create_window(
            width // 2,
            height // 2,
            window=self.body,
            width=width - 2 * gap,
            height=height - 2 * gap,
        )

    def setRing(self, colour):
        """Change the colour of the ring around the card."""
        self.itemconfig("ring", fill=colour)


def makeEntry(
    parent,
    variable,
    width,
    background=CARD,
    size=13,
    justify="left",
    height=46,
    fill=BG,
):
    """Create a pill-shaped text box.

    background is the colour behind the box, fill is the box's own colour.
    Returns (the card to pack, the Entry to read from).
    """
    box = Card(
        parent,
        width=width,
        height=height,
        radius=height // 2,
        fill=fill,
        background=background,
    )
    entry = tk.Entry(
        box.body,
        textvariable=variable,
        font=(FONT, size),
        justify=justify,
        bg=fill,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        highlightthickness=0,
        disabledbackground=fill,
        disabledforeground=MUTED,
    )
    entry.pack(fill="both", expand=True, padx=12)
    entry.bind("<FocusIn>", lambda event: box.setRing(ACCENT))
    entry.bind("<FocusOut>", lambda event: box.setRing(background))
    return box, entry


def soundLabel():
    """Return the text for the sound button."""
    return "Sound: on" if sound_on else "Sound: off"


def playSound(name):
    """Play a short sound from the sounds folder without freezing the window."""
    path = SOUNDS_DIR / name
    if not sound_on or not path.exists():
        return

    try:
        if sys.platform == "win32":
            import winsound

            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", str(path)])
        else:
            subprocess.Popen(["aplay", "-q", str(path)])
    except (OSError, RuntimeError):
        pass  # a missing sound player must never stop the quiz


def loadLeaderboard():
    """Read the leaderboard file: {level as text: list of score entries}."""
    board = {str(level): [] for level in DIFFICULTY_LEVELS}

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return board  # missing or damaged file: start empty

    if isinstance(saved, dict):
        for level in board:
            if level in saved:
                board[level] = saved[level]
    return board


def saveLeaderboard(board):
    """Write the leaderboard to the file. Returns False if it can't be written."""
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
            json.dump(board, file, indent=2)
    except OSError:
        return False
    return True


def addScore(board, level, name, score, best_streak):
    """Add a result to the board, keeping only the top scores.

    Returns (rank, entry). The rank is 1 for the top spot, or None if the
    score didn't make the list.
    """
    entries = board[str(level)]
    entry = {"name": name, "score": score, "streak": best_streak}
    entries.append(entry)

    # sort is stable, so on a tie the older score stays higher
    entries.sort(key=lambda item: item["score"], reverse=True)
    del entries[MAX_SCORES:]

    for position, item in enumerate(entries, start=1):
        if item is entry:
            return position, entry
    return None, entry


class MathsQuiz:
    """The quiz window and its state."""

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.setupStyle()

        self.name_var = tk.StringVar()  # keeps the name when the screen is redrawn
        self.leaderboard = loadLeaderboard()

        self.resetQuiz()
        self.displayMenu()

    def setupStyle(self):
        """Set the window colour and the default colours of labels and frames."""
        self.root.configure(bg=BG)
        self.root.option_add("*Label.background", BG)
        self.root.option_add("*Label.foreground", TEXT)
        self.root.option_add("*Frame.background", BG)

    def resetQuiz(self):
        """Reset the quiz state ready for a new quiz."""
        self.difficulty = None
        self.question_number = 0
        self.score = 0
        self.streak = 0  # correct first attempts in a row
        self.best_streak = 0
        self.attempt = 1
        self.num1 = 0
        self.num2 = 0
        self.operation = "+"
        self.correct_answer = 0
        self.time_left = 0
        self.timer_job = None  # pending root.after id, so it can be cancelled
        self.history = []  # one dict per finished question
        self.current_answers = []  # answers given for the current question
        self.player_name = DEFAULT_NAME
        self.rank = None
        self.last_entry = None  # latest result, so its leaderboard row is highlighted
        self.saved_ok = True

    def clearWindow(self):
        """Remove every widget so a new screen can be drawn."""
        self.cancelTimer()
        for widget in self.root.winfo_children():
            widget.destroy()

    def drawBackground(self, page):
        """Draw the faint maths symbols in the space around the page.

        A symbol that would run behind the page is skipped, because the page
        frame would cut it off.
        """
        self.root.update_idletasks()
        left, top = page.winfo_x(), page.winfo_y()
        right, bottom = left + page.winfo_width(), top + page.winfo_height()

        background = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        background.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.lower(background)  # behind the page (Canvas has its own lower())

        for symbol, x, y, size, tilt in SYMBOLS:
            reach = size  # roughly how far the symbol extends from its centre
            behind_page = (
                left < x + reach
                and x - reach < right
                and top < y + reach
                and y - reach < bottom
            )
            if not behind_page:
                background.create_text(
                    x,
                    y,
                    text=symbol,
                    fill=SYMBOL,
                    font=(FONT_LIGHT, size),
                    angle=tilt,
                )

    def displayMenu(self):
        """Show the name box and the difficulty buttons."""
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Maths Quiz", font=(FONT_LIGHT, 44)).pack()
        tk.Label(
            page,
            text=f"{TOTAL_QUESTIONS} questions \u00b7 two attempts \u00b7 beat the clock",
            font=(FONT, 11),
            fg=MUTED,
        ).pack(pady=(6, 34))

        box, entry = makeEntry(
            page, self.name_var, width=380, height=50, background=BG, fill=CARD
        )
        box.pack(pady=(0, 26))

        # hint text placed over the empty name box
        hint = tk.Label(entry, text="Your name", font=(FONT, 13), fg=MUTED, bg=CARD)
        hint.bind("<Button-1>", lambda event: entry.focus_set())

        def updateHint(event=None):
            """Show the hint only while the name box is empty."""
            if entry.get():
                hint.place_forget()
            else:
                hint.place(x=2, y=0, relheight=1)

        entry.bind("<KeyRelease>", updateHint)
        updateHint()

        # level=level fixes the value for each button
        for level, name in DIFFICULTY_LEVELS.items():
            RoundedButton(
                page,
                name,
                lambda level=level: self.selectDifficulty(level),
                width=380,
                height=50,
                hint=DIFFICULTY_HINTS[level],
                fill=CARD,
                hover=ACCENT,
                text_colour=TEXT,
                background=BG,
            ).pack(pady=4)

        extras = tk.Frame(page)
        extras.pack(pady=(30, 0))

        RoundedButton(
            extras,
            "View leaderboard",
            lambda: self.displayLeaderboard(1, self.displayMenu),
            width=200,
            height=48,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
        ).pack(side="left", padx=(0, 8))

        sound_button = RoundedButton(
            extras,
            soundLabel(),
            lambda: self.toggleSound(sound_button),
            width=172,
            height=48,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
        )
        sound_button.pack(side="left")

        self.drawBackground(page)

    def toggleSound(self, button):
        """Switch the sound effects on or off and update the button text."""
        global sound_on
        sound_on = not sound_on
        button.itemconfig(button.label, text=soundLabel())

    def selectDifficulty(self, level):
        """Start a new quiz at the chosen level."""
        name = self.name_var.get().strip()[:MAX_NAME_LENGTH] or DEFAULT_NAME

        self.resetQuiz()
        self.difficulty = level
        self.player_name = name
        self.generateQuestion()
        self.displayProblem()

    def randomInt(self, difficulty):
        """Return a random number in the range for this difficulty."""
        minimum, maximum = DIFFICULTY_RANGES[difficulty]
        return random.randint(minimum, maximum)

    def decideOperation(self):
        """Return '+' or '-' at random."""
        return random.choice(["+", "-"])

    def operationSymbol(self):
        """Return the sign to display: a proper minus sign instead of a hyphen."""
        return "\u2212" if self.operation == "-" else "+"

    def generateQuestion(self):
        """Create a new question and its answer."""
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

    def displayProblem(self):
        """Show the current question."""
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        top = tk.Frame(page)
        top.pack(fill="x")
        tk.Label(
            top,
            text=f"Question {self.question_number} of {TOTAL_QUESTIONS}",
            font=(FONT, 11),
            fg=MUTED,
        ).pack(side="left")
        self.timer_label = tk.Label(top, text="", font=(FONT, 11))
        self.timer_label.pack(side="right")

        bar = tk.Canvas(page, width=QUESTION_WIDTH, height=4, highlightthickness=0)
        bar.pack(pady=(12, 36))
        roundedRectangle(bar, 0, 0, QUESTION_WIDTH, 4, 2, CARD, "track")
        done = QUESTION_WIDTH * self.question_number // TOTAL_QUESTIONS
        roundedRectangle(bar, 0, 0, done, 4, 2, ACCENT, "done")

        self.attempt_label = tk.Label(page, text="", font=(FONT, 10, "bold"))
        self.attempt_label.pack()

        equation = tk.Frame(page)
        equation.pack(pady=(4, 0))
        parts = [
            (str(self.num1), TEXT),
            (self.operationSymbol(), ACCENT_SOFT),
            (str(self.num2), TEXT),
            ("=", MUTED),
            ("?", ACCENT_SOFT),
        ]
        for text, colour in parts:
            tk.Label(
                equation,
                text=text,
                fg=colour,
                font=(FONT_LIGHT, QUESTION_SIZES[self.difficulty]),
            ).pack(side="left", padx=6)

        box, self.answer_entry = makeEntry(
            page,
            None,
            width=260,
            size=26,
            justify="center",
            height=66,
            background=BG,
            fill=CARD,
        )
        box.pack(pady=(30, 0))
        self.answer_entry.focus_set()
        self.answer_entry.bind("<Return>", lambda event: self.checkAnswer())

        self.feedback_label = tk.Label(page, text="", font=(FONT, 12))
        self.feedback_label.pack(pady=(14, 10))

        self.submit_button = RoundedButton(
            page,
            "Submit",
            self.checkAnswer,
            width=200,
            height=52,
            background=BG,
        )
        self.submit_button.pack()

        stats = tk.Frame(page)
        stats.pack(pady=(44, 0))
        self.streak_label = self.makeStat(stats, "Streak")
        self.score_label = self.makeStat(stats, "Score")
        self.best_label = self.makeStat(stats, "Best")

        self.updateAttemptLabel()
        self.updateStats()
        self.startTimer()
        self.drawBackground(page)

    def makeStat(self, parent, caption):
        """Add a 'caption value' pair of labels. Returns the value label."""
        pair = tk.Frame(parent)
        pair.pack(side="left", padx=20)
        tk.Label(pair, text=caption, font=(FONT, 11), fg=MUTED).pack(
            side="left", padx=(0, 6)
        )
        value = tk.Label(pair, text="0", font=(FONT, 11, "bold"))
        value.pack(side="left")
        return value

    def updateAttemptLabel(self):
        """Show LAST CHANCE on the second attempt only."""
        if self.attempt == 1:
            self.attempt_label.config(text=" ")
        else:
            self.attempt_label.config(text="LAST CHANCE", fg=WARN)

    def updateStats(self):
        """Refresh the streak, score and best streak."""
        self.score_label.config(text=str(self.score))

        colour = SUCCESS if self.streak >= STREAK_HIGHLIGHT else TEXT
        self.streak_label.config(text=str(self.streak), fg=colour)
        self.best_label.config(text=str(self.best_streak))

    def startTimer(self):
        """Start the countdown for the current attempt."""
        self.cancelTimer()
        self.time_left = TIME_LIMITS[self.difficulty]
        self.drawTimer()
        self.timer_job = self.root.after(1000, self.tick)

    def tick(self):
        """Count down one second, and time out at zero."""
        self.time_left -= 1
        self.drawTimer()

        if self.time_left <= 0:
            self.timeUp()
        else:
            self.timer_job = self.root.after(1000, self.tick)

    def cancelTimer(self):
        """Stop the countdown if one is running."""
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    def drawTimer(self):
        """Show the seconds left, in red when time is nearly up."""
        colour = ERROR if self.time_left <= WARNING_SECONDS else MUTED
        self.timer_label.config(text=f"{max(self.time_left, 0)} s", fg=colour)

    def timeUp(self):
        """Count running out of time as a wrong attempt."""
        self.timer_job = None
        self.current_answers.append(None)  # None = no answer given
        playSound("wrong.wav")

        if self.attempt == 1:
            self.feedback_label.config(text="Time's up! Try once more!", fg=WARN)
        else:
            self.feedback_label.config(
                text=f"Time's up! The answer was {self.correct_answer}.", fg=ERROR
            )
        self.handleMiss()

    def checkAnswer(self):
        """Handle Submit: validate the input, check it and score it."""
        # ignore Enter while the inputs are locked between questions
        if str(self.answer_entry.cget("state")) == "disabled":
            return

        text = self.answer_entry.get().strip()

        # int() accepts negatives like "-54" and rejects empty or text input
        try:
            user_answer = int(text)
        except ValueError:
            self.feedback_label.config(text="Please enter a whole number.", fg=ERROR)
            self.answer_entry.focus_set()
            return  # invalid input does not use up an attempt

        self.current_answers.append(user_answer)

        if self.isCorrect(user_answer, self.correct_answer, self.attempt):
            self.score += POINTS_PER_ATTEMPT[self.attempt]

            # only a first-attempt answer extends the streak
            if self.attempt == 1:
                self.streak += 1
                self.best_streak = max(self.best_streak, self.streak)

            self.updateStats()
            self.recordQuestion(POINTS_PER_ATTEMPT[self.attempt])
            self.finishQuestion()
        else:
            self.handleMiss()

    def isCorrect(self, user_answer, correct_answer, attempt):
        """Check the answer and show the feedback. Returns True if it was correct."""
        if user_answer == correct_answer:
            points = POINTS_PER_ATTEMPT[attempt]
            self.feedback_label.config(text=f"Correct! +{points} points", fg=SUCCESS)
            playSound("correct.wav")
            return True

        if attempt == 1:
            self.feedback_label.config(text="Not quite. Try once more!", fg=WARN)
        else:
            self.feedback_label.config(
                text=f"Wrong. The answer was {correct_answer}.", fg=ERROR
            )
        playSound("wrong.wav")
        return False

    def handleMiss(self):
        """Handle a wrong answer or a timeout."""
        if self.attempt == 1:
            # missing the first attempt ends the streak and gives a second go
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
        """Save a finished question for the review screen."""
        self.history.append(
            {
                "question": f"{self.num1} {self.operationSymbol()} {self.num2} =",
                "answers": list(self.current_answers),
                "correct": self.correct_answer,
                "points": points,
            }
        )

    def finishQuestion(self):
        """Lock the inputs while the feedback is read, then move on."""
        self.cancelTimer()
        self.answer_entry.config(state="disabled")
        self.submit_button.setEnabled(False)
        self.root.after(FEEDBACK_DELAY_MS, self.nextQuestion)

    def nextQuestion(self):
        """Show the next question, or finish after the last one."""
        if self.question_number < TOTAL_QUESTIONS:
            self.generateQuestion()
            self.displayProblem()
        else:
            self.finishQuiz()

    def finishQuiz(self):
        """Add the score to the leaderboard, save it and show the results."""
        self.rank, self.last_entry = addScore(
            self.leaderboard,
            self.difficulty,
            self.player_name,
            self.score,
            self.best_streak,
        )
        self.saved_ok = saveLeaderboard(self.leaderboard)
        playSound("highscore.wav" if self.rank == 1 else "finish.wav")
        self.displayResults(self.score)

    def getGrade(self, score):
        """Return the letter grade for a score out of 100."""
        for minimum, grade in GRADE_BOUNDARIES:
            if score >= minimum:
                return grade

    def displayResults(self, score):
        """Show the final score and grade."""
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        level_name = DIFFICULTY_LEVELS[self.difficulty]
        tk.Label(
            page,
            text=f"{self.player_name} \u00b7 {level_name}",
            font=(FONT, 11),
            fg=MUTED,
        ).pack()

        tk.Label(page, text=str(score), font=(FONT_LIGHT, 110)).pack(pady=(10, 0))
        tk.Label(
            page, text=f"out of {TOTAL_QUESTIONS * 10}", font=(FONT, 12), fg=MUTED
        ).pack()

        if self.rank == 1:
            message, colour = "New high score!", WARN
        elif self.rank is not None:
            message = f"You placed #{self.rank} on the {level_name} leaderboard."
            colour = TEXT
        else:
            message, colour = "Not on the leaderboard this time.", MUTED

        if not self.saved_ok:
            message += " (The leaderboard file couldn't be saved.)"

        tk.Label(page, text=message, font=(FONT, 12), fg=colour).pack(pady=(22, 0))

        stats = tk.Frame(page)
        stats.pack(pady=(22, 40))
        self.makeStat(stats, "Best streak").config(text=str(self.best_streak))
        self.makeStat(stats, "Grade").config(text=self.getGrade(score), fg=ACCENT_SOFT)

        buttons = tk.Frame(page)
        buttons.pack()

        RoundedButton(
            buttons, "Review answers", self.displayReview, width=150, height=48
        ).pack(side="left", padx=6)

        quiet = dict(
            width=150,
            height=48,
            fill=CARD,
            hover=CARD_HOVER,
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

        self.drawBackground(page)

    def displayReview(self):
        """Show every question with the answers given and the correct answer."""
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Review", font=(FONT_LIGHT, 40)).pack()
        tk.Label(
            page,
            text=f"{self.player_name} \u00b7 {DIFFICULTY_LEVELS[self.difficulty]}"
            f" \u00b7 {self.score} out of {TOTAL_QUESTIONS * 10}",
            font=(FONT, 11),
            fg=MUTED,
        ).pack(pady=(2, 16))

        # the heading and every row share these column widths
        widths = [40, 190, 170, 100, 80]
        headings = ["", "QUESTION", "YOUR ANSWER", "CORRECT", "POINTS"]

        table = tk.Frame(page)
        table.pack()
        for column, width in enumerate(widths):
            table.columnconfigure(column, minsize=width)

        for column, heading in enumerate(headings):
            tk.Label(
                table,
                text=heading,
                font=(FONT, 9, "bold"),
                fg=MUTED,
                anchor="w",
            ).grid(row=0, column=column, sticky="w", pady=(0, 8))

        for number, record in enumerate(self.history, start=1):
            points = record["points"]
            if points == POINTS_PER_ATTEMPT[1]:
                points_colour, icon = SUCCESS, "\u2713"
            elif points > 0:
                points_colour, icon = WARN, "\u2713"  # right, but on the second try
            else:
                points_colour, icon = ERROR, "\u2717"

            # "4, 3" means the first answer was 4 and the second was 3
            given = ", ".join(
                "-" if answer is None else str(answer) for answer in record["answers"]
            )

            values = [icon, record["question"], given, record["correct"], points]
            for column, value in enumerate(values):
                colour = points_colour if column in (0, 4) else TEXT
                tk.Label(
                    table,
                    text=value,
                    font=(FONT, 12),
                    fg=colour,
                    anchor="w",
                ).grid(row=number, column=column, sticky="w", pady=4)

        RoundedButton(
            page,
            "Back to results",
            lambda: self.displayResults(self.score),
            width=200,
            height=48,
        ).pack(pady=(26, 0))

        self.drawBackground(page)

    def displayLeaderboard(self, level, back):
        """Show the top scores for one level. back is run by the Back button."""
        self.clearWindow()

        page = tk.Frame(self.root)
        page.pack(expand=True)

        tk.Label(page, text="Leaderboard", font=(FONT_LIGHT, 40)).pack(pady=(0, 18))

        # one tab per level; the current one is filled
        tabs = tk.Frame(page)
        tabs.pack(pady=(0, 26))
        for tab_level, name in DIFFICULTY_LEVELS.items():
            chosen = tab_level == level
            RoundedButton(
                tabs,
                name,
                lambda tab_level=tab_level: self.displayLeaderboard(tab_level, back),
                width=120,
                height=38,
                fill=ACCENT if chosen else CARD,
                hover=ACCENT_HOVER if chosen else CARD_HOVER,
                text_colour="white" if chosen else MUTED,
            ).pack(side="left", padx=4)

        entries = self.leaderboard[str(level)]

        # the heading and every row share these column widths
        widths = [50, 220, 100, 110]
        headings = ["#", "PLAYER", "SCORE", "BEST STREAK"]

        table = tk.Frame(page)
        table.pack()
        for column, width in enumerate(widths):
            table.columnconfigure(column, minsize=width)

        for column, heading in enumerate(headings):
            tk.Label(
                table,
                text=heading,
                font=(FONT, 9, "bold"),
                fg=MUTED,
                anchor="w",
            ).grid(row=0, column=column, sticky="w", pady=(0, 8))

        # always list MAX_SCORES places, so the screen keeps its size
        for position in range(1, MAX_SCORES + 1):
            entry = entries[position - 1] if position <= len(entries) else None
            if entry is None:
                values = [position, "-", "-", "-"]
            else:
                values = [position, entry["name"], entry["score"], entry["streak"]]

            latest = entry is not None and entry is self.last_entry
            for column, value in enumerate(values):
                if entry is None:
                    colour = MUTED
                elif position == 1 and column == 0:
                    colour = WARN
                else:
                    colour = ACCENT_SOFT if latest else TEXT
                tk.Label(
                    table,
                    text=value,
                    fg=colour,
                    anchor="w",
                    font=(FONT, 13, "bold" if latest else "normal"),
                ).grid(row=position, column=column, sticky="w", pady=6)

        RoundedButton(page, "Back", back, width=160, height=48).pack(pady=(30, 0))

        self.drawBackground(page)

    def playAgain(self):
        """Go back to the menu for a new quiz."""
        self.resetQuiz()
        self.displayMenu()

    def quitQuiz(self):
        """Close the application."""
        self.cancelTimer()
        self.root.destroy()


def main():
    """Create the Tkinter root window and start the event loop."""
    root = tk.Tk()
    MathsQuiz(root)
    root.mainloop()


if __name__ == "__main__":
    main()
