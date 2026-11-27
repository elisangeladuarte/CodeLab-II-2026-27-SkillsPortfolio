# AI acknowledgement: this program was developed with help from Claude
# Prompts used:
# "Redesign the student manager with a light, professional theme"
# "Make the window smaller so it fits on a laptop screen"

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

WINDOW_TITLE = "Student Manager"
WINDOW_SIZE = "1100x686"

# Build the path from this script's location so it works from any folder
DATA_FILE = Path(__file__).parent / "studentMarks.txt"

# Maximum marks available (3 coursework marks of 20, plus an exam out of 100)
MAX_COURSEWORK_MARK = 20
MAX_EXAM_MARK = 100
COURSEWORK_COUNT = 3
MAX_TOTAL = COURSEWORK_COUNT * MAX_COURSEWORK_MARK + MAX_EXAM_MARK  # 160

# Grade boundaries: (minimum percentage, grade), checked from highest to lowest
GRADE_BOUNDARIES = [(70, "A"), (60, "B"), (50, "C"), (40, "D"), (0, "F")]

# Valid range for a student code, and the number of comma-separated fields
# on each line: code, name, three coursework marks, exam
MIN_CODE = 1000
MAX_CODE = 9999
FIELDS_PER_LINE = COURSEWORK_COUNT + 3

# Maximum number of file problems listed in the warning popup
MAX_PROBLEMS_SHOWN = 5

MAX_UNDO = 10

# Table columns: (heading, width in pixels, text alignment). The widths add up
# to 1012 pixels, which is the room inside the table card.
TABLE_COLUMNS = [
    ("Name", 250, "w"),
    ("Number", 110, "center"),
    ("Coursework /60", 160, "center"),
    ("Exam /100", 130, "center"),
    ("Percentage", 230, "center"),
    ("Grade", 132, "center"),
]
TABLE_WIDTH = sum(width for _, width, _ in TABLE_COLUMNS)

# Colours
BG = "#F3F5F9"
CARD = "#FFFFFF"
BORDER = "#E1E6EE"
LINE = "#EDF0F5"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
ACCENT_SOFT = "#EFF4FF"
TEXT = "#1B2A41"
MUTED = "#6B7A90"
ERROR = "#DC2626"
ERROR_HOVER = "#B91C1C"
SUCCESS = "#16A34A"
OFF = "#A5B0C0"
WHITE = "#FFFFFF"

GRADE_COLOURS = {
    "A": "#DCFCE7",
    "B": "#DBEAFE",
    "C": "#FEF3C7",
    "D": "#FFEDD5",
    "F": "#FEE2E2",
}
GRADE_BAR_COLOURS = {
    "A": "#16A34A",
    "B": "#2563EB",
    "C": "#D97706",
    "D": "#EA580C",
    "F": "#DC2626",
}

FONT = "Segoe UI"
FONT_LIGHT = "Segoe UI Light"
STAT_WIDTH = 230
STAT_HEIGHT = 128
CHART_CARD_WIDTH = 294
CHART_SIZE = (276, 110)
TABLE_CARD_SIZE = (1032, 326)  # the white card that holds the table
HEADER_HEIGHT = 40  # the row of column headings
TABLE_ROWS_HEIGHT = 266  # room for seven rows (326 - 20 margins - 40 heading)
ROW_HEIGHT = 38  # one student row
PROGRESS_WIDTH = 90  # the length of the percentage bar
MAX_CHOICES = 6  # students listed at once in the pick-a-student pop-up

# Sort choices: label shown to the user -> function that gives the sort key
SORT_KEYS = {
    "Name": lambda student: student.name.lower(),
    "Student number": lambda student: student.code,
    "Coursework total": lambda student: student.coursework_total,
    "Exam mark": lambda student: student.exam,
    "Overall percentage": lambda student: student.percentage,
}

# Table heading -> (sort key name from SORT_KEYS, True if the first click sorts high to low)
COLUMN_SORT = {
    "Name": ("Name", False),
    "Number": ("Student number", False),
    "Coursework /60": ("Coursework total", True),
    "Exam /100": ("Exam mark", True),
    "Percentage": ("Overall percentage", True),
    "Grade": (
        "Overall percentage",
        True,
    ),  # grades follow the percentage, so A is first
}


def roundedRectangle(canvas, x1, y1, x2, y2, radius, fill, tag):
    """Draw a filled rectangle with rounded corners on a canvas."""
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


def drawOutlinedShape(canvas, width, height, radius, fill, edge):
    """Draw a rounded shape with a thin outline."""
    roundedRectangle(canvas, 0, 0, width, height, radius, edge, "edge")
    roundedRectangle(canvas, 1, 1, width - 1, height - 1, radius - 1, fill, "shape")


class RoundedButton(tk.Canvas):
    """A clickable pill-shaped button, drawn on a canvas."""

    def __init__(
        self,
        parent,
        text,
        command,
        width=120,
        height=38,
        fill=CARD,
        hover=ACCENT_SOFT,
        text_colour=TEXT,
        outline=BORDER,
        background=BG,
        bold=False,
        align="center",
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
        self.outline = outline  # None means no outline
        self.background = background
        self.enabled = True
        self.active = False

        drawOutlinedShape(self, width, height, height // 2, fill, outline or fill)
        text_x, anchor = (18, "w") if align == "w" else (width // 2, "center")
        self.label = self.create_text(
            text_x,
            height // 2,
            text=text,
            anchor=anchor,
            fill=text_colour,
            font=(FONT, 11, "bold" if bold else "normal"),
        )

        self.bind("<Enter>", lambda event: self.refresh(True))
        self.bind("<Leave>", lambda event: self.refresh(False))
        self.bind("<Button-1>", self.click)

    def paint(self, fill, edge, text):
        """Set the three colours of the button: inside, outline and text."""
        self.itemconfig("shape", fill=fill)
        self.itemconfig("edge", fill=edge)
        self.itemconfig(self.label, fill=text)

    def refresh(self, hovering=False):
        """Colour the button for its current state."""
        if not self.enabled:
            self.paint(self.background, BORDER, OFF)
        elif self.active:
            colour = ACCENT_HOVER if hovering else ACCENT
            self.paint(colour, colour, WHITE)
        else:
            inside = self.hover if hovering else self.fill
            self.paint(inside, self.outline or inside, self.text_colour)

    def click(self, event):
        """Run the button's command (unless the button is disabled)."""
        if self.enabled:
            self.command()

    def setEnabled(self, enabled):
        """Turn the button on or off. A disabled button looks greyed out."""
        self.enabled = enabled
        self.config(cursor="hand2" if enabled else "arrow")
        self.refresh()

    def setActive(self, active):
        """Highlight the button in blue, to show it is the chosen option."""
        self.active = active
        self.refresh()


class Card(tk.Canvas):
    """A white rounded panel. Put other widgets inside it using its .body frame."""

    def __init__(
        self, parent, width, height, radius=22, fill=CARD, background=BG, border=BORDER
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=background,
            highlightthickness=0,
        )
        drawOutlinedShape(self, width, height, radius, fill, border or fill)

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

    def setEdge(self, colour):
        """Change the colour of the outline (used for the focus highlight)."""
        self.itemconfig("edge", fill=colour)


def makeEntry(parent, variable, width, height=42, size=12, fill=CARD, background=BG):
    """Create a pill-shaped text box that gets a blue outline when it is clicked."""
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
        bg=fill,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        highlightthickness=0,
        disabledbackground=fill,
        disabledforeground=MUTED,
    )
    entry.pack(fill="both", expand=True, padx=8)
    entry.bind("<FocusIn>", lambda event: box.setEdge(ACCENT))
    entry.bind("<FocusOut>", lambda event: box.setEdge(BORDER))
    return box, entry


class Student:
    """One student's record, with marks and calculated results."""

    def __init__(self, code, name, coursework, exam):
        """Create a student record."""
        self.code = code
        self.name = name
        self.coursework = coursework
        self.exam = exam

    @property
    def coursework_total(self):
        """int: the sum of the three coursework marks (out of 60)."""
        return sum(self.coursework)

    @property
    def total(self):
        """int: coursework total plus exam mark (out of 160)."""
        return self.coursework_total + self.exam

    @property
    def percentage(self):
        """float: the overall percentage, based on the 160 available marks."""
        return self.total / MAX_TOTAL * 100

    @property
    def grade(self):
        """str: the letter grade for the overall percentage."""
        for minimum, grade in GRADE_BOUNDARIES:
            if self.percentage >= minimum:
                return grade

    def __str__(self):
        """Return a one-line summary, handy for debugging."""
        return (
            f"{self.code} {self.name}: {self.total}/{MAX_TOTAL} "
            f"({self.percentage:.1f}%) grade {self.grade}"
        )


def parseStudent(line):
    """Convert one line of the file into a Student."""
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != FIELDS_PER_LINE:
        raise ValueError(f"expected {FIELDS_PER_LINE} fields but found {len(parts)}")

    code_text, name, *mark_texts = parts

    code = int(code_text)
    if not MIN_CODE <= code <= MAX_CODE:
        raise ValueError(f"code {code} is not between {MIN_CODE} and {MAX_CODE}")

    if not name:
        raise ValueError("the student name is empty")

    coursework = [int(mark) for mark in mark_texts[:COURSEWORK_COUNT]]
    exam = int(mark_texts[-1])

    if any(not 0 <= mark <= MAX_COURSEWORK_MARK for mark in coursework):
        raise ValueError(f"coursework marks must be 0-{MAX_COURSEWORK_MARK}")
    if not 0 <= exam <= MAX_EXAM_MARK:
        raise ValueError(f"the exam mark must be 0-{MAX_EXAM_MARK}")

    return Student(code, name, coursework, exam)


def loadStudents(path):
    """Read the data file once and return every valid student record."""
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

                # The first non-blank line holds the number of students
                if not header_read:
                    header_read = True
                    try:
                        expected_count = int(line)
                    except ValueError:
                        problems.append(
                            f"Line {line_number}: the first line should be "
                            "the number of students."
                        )
                    continue

                try:
                    student = parseStudent(line)
                except ValueError as error:
                    problems.append(f"Line {line_number}: {error}")
                    continue

                if student.code in codes_seen:
                    problems.append(
                        f"Line {line_number}: duplicate code {student.code}."
                    )
                    continue

                codes_seen.add(student.code)
                students.append(student)
    except FileNotFoundError:
        problems.append(f"Could not find the data file: {path}")
    except (OSError, UnicodeDecodeError) as error:
        problems.append(f"The data file could not be read: {error}")

    if expected_count is not None and expected_count != len(students):
        problems.append(
            f"The file says {expected_count} students but "
            f"{len(students)} valid records were loaded."
        )

    return students, problems


def saveStudents(path, students):
    """Write all students back to the data file."""
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
    """Validate raw form input and return a Student."""
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
    """Return the average overall percentage for a list of students."""
    if not students:
        return 0.0
    return sum(student.percentage for student in students) / len(students)


def findExtremes(students, highest=True):
    """Return every student who shares the highest (or lowest) total mark."""
    if not students:
        return []

    pick = max if highest else min
    target = pick(student.total for student in students)
    return [student for student in students if student.total == target]


def sortStudents(students, key_name, descending=False):
    """Return a sorted copy of a list of students."""
    return sorted(students, key=SORT_KEYS[key_name], reverse=descending)


def countGrades(students):
    """Count how many students got each grade."""
    counts = {grade: 0 for _, grade in GRADE_BOUNDARIES}
    for student in students:
        counts[student.grade] += 1
    return counts


def searchStudents(students, text):
    """Return the students whose name or student code contains the text."""
    text = text.lower()
    return [
        student
        for student in students
        if text in student.name.lower() or text in str(student.code)
    ]


class StudentManager:
    """Main application class: holds the window and the student records."""

    def __init__(self, root):
        """Set up the main window and load the student data."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.setupStyle()

        self.students, problems = loadStudents(DATA_FILE)
        if problems:
            self.reportProblems(problems)

        self.shown_students = []
        self.sort_column = None
        self.sort_descending = False

        self.undo_stack = []

        self.search_var = tk.StringVar()
        self.ignore_search = False  # True while the program itself changes the text
        self.search_var.trace_add("write", self.onSearchChange)

        self.createWidgets()

    def setupStyle(self):
        """Apply the light theme to the window and the default widget colours."""
        self.root.configure(bg=BG)

        defaults = {
            "*Font": f"{{{FONT}}} 11",
            "*Label.background": BG,
            "*Label.foreground": TEXT,
            "*Frame.background": BG,
        }
        for pattern, value in defaults.items():
            self.root.option_add(pattern, value)

    def createHeader(self, parent):
        """Build the top row: the title on the left (the search box joins it later)."""
        self.header = tk.Frame(parent)
        self.header.pack(fill="x", padx=34, pady=(26, 0))

        tk.Label(self.header, text="Student Manager", font=(FONT_LIGHT, 30)).pack(
            side="left"
        )

    def createStats(self, parent):
        """Build the row of cards: average, highest, lowest and the grade chart."""
        row = tk.Frame(parent)
        row.pack(fill="x", padx=34, pady=(18, 0))

        self.stat_labels = {}
        for key, caption in (
            ("average", "AVERAGE"),
            ("highest", "HIGHEST"),
            ("lowest", "LOWEST"),
        ):
            card = Card(row, width=STAT_WIDTH, height=STAT_HEIGHT)
            card.pack(side="left", padx=(0, 16))

            tk.Label(
                card.body,
                text=caption,
                font=(FONT, 9, "bold"),
                fg=MUTED,
                bg=CARD,
                anchor="w",
            ).pack(fill="x", padx=10, pady=(6, 0))
            value = tk.Label(
                card.body, text="", font=(FONT_LIGHT, 30), bg=CARD, anchor="w"
            )
            value.pack(fill="x", padx=10)
            detail = tk.Label(
                card.body, text="", font=(FONT, 10), fg=MUTED, bg=CARD, anchor="w"
            )
            detail.pack(fill="x", padx=10)
            self.stat_labels[key] = (value, detail)

        chart_card = Card(row, width=CHART_CARD_WIDTH, height=STAT_HEIGHT)
        chart_card.pack(side="left")
        self.grade_chart = tk.Canvas(
            chart_card.body,
            width=CHART_SIZE[0],
            height=CHART_SIZE[1],
            bg=CARD,
            highlightthickness=0,
        )
        self.grade_chart.pack()

    def updateStats(self):
        """Refresh the three stat cards and the chart from the whole class."""
        self.drawGradeChart()

        if not self.students:
            for value, detail in self.stat_labels.values():
                value.config(text="-", fg=TEXT)
                detail.config(text="no students")
            return

        count = len(self.students)
        noun = "student" if count == 1 else "students"
        value, detail = self.stat_labels["average"]
        value.config(text=f"{averagePercentage(self.students):.1f}%", fg=TEXT)
        detail.config(text=f"across {count} {noun}")

        self.setStat("highest", findExtremes(self.students, True), SUCCESS)
        self.setStat("lowest", findExtremes(self.students, False), ERROR)

    def setStat(self, key, matches, colour):
        """Fill in a highest or lowest card."""
        value, detail = self.stat_labels[key]
        name = matches[0].name
        if len(matches) > 1:
            name += f" +{len(matches) - 1} more"  # a tie
        value.config(text=f"{matches[0].percentage:.1f}%", fg=colour)
        detail.config(text=name)

    def drawGradeChart(self):
        """Draw one rounded bar for each grade, showing how many students got it."""
        canvas = self.grade_chart
        canvas.delete("all")
        width, height = CHART_SIZE

        counts = countGrades(self.students)
        biggest = max(max(counts.values()), 1)  # avoids dividing by zero

        top = 20
        baseline = height - 22
        plot_height = baseline - top
        slot = width / len(counts)
        bar_width = slot * 0.5

        for position, (grade, count) in enumerate(counts.items()):
            left = position * slot + (slot - bar_width) / 2
            centre = left + bar_width / 2

            if count > 0:
                bar_height = max(plot_height * count / biggest, 8)
                colour = GRADE_BAR_COLOURS[grade]
            else:
                bar_height = 3  # a thin pale line, so the grade is still shown
                colour = GRADE_COLOURS[grade]

            roundedRectangle(
                canvas,
                left,
                baseline - bar_height,
                left + bar_width,
                baseline,
                5,
                colour,
                "bar",
            )
            canvas.create_text(
                centre,
                baseline - bar_height - 9,
                text=str(count),
                fill=TEXT,
                font=(FONT, 10, "bold"),
            )
            canvas.create_text(
                centre, height - 9, text=grade, fill=MUTED, font=(FONT, 10)
            )

    def reportProblems(self, problems):
        """Show a warning listing the first few problems found in the file."""
        shown = problems[:MAX_PROBLEMS_SHOWN]
        message = "\n".join(shown)
        if len(problems) > MAX_PROBLEMS_SHOWN:
            message += f"\n...and {len(problems) - MAX_PROBLEMS_SHOWN} more."
        messagebox.showwarning("Problems with the data file", message)

    def createWidgets(self):
        """Build the title and search box, the stat cards, the menu and the table."""
        self.createHeader(self.root)
        self.createSearch(self.header)
        self.createStats(self.root)
        self.createMenu(self.root)
        self.createTableArea(self.root)

        self.summary_label = tk.Label(
            self.root,
            text="Choose an option from the menu.",
            font=(FONT, 11),
            anchor="w",
        )
        self.summary_label.pack(fill="x", padx=36, pady=(10, 0))

        self.updateStats()

        # Without any data there is nothing to show
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            self.search_entry.config(state="disabled")
        else:
            self.runOption(self.viewAll, "View all")

    def createSearch(self, parent):
        """Build the search box on the right of the header."""
        box, self.search_entry = makeEntry(
            parent, self.search_var, width=340, height=42
        )
        box.pack(side="right")

        # Grey hint text on top of the empty box, and a small cross to clear it
        hint = tk.Label(
            self.search_entry,
            text="Search name or number...",
            font=(FONT, 12),
            fg=MUTED,
            bg=CARD,
        )
        hint.bind("<Button-1>", lambda event: self.search_entry.focus_set())

        cross = tk.Label(
            self.search_entry,
            text="✕",
            font=(FONT, 11),
            fg=MUTED,
            bg=CARD,
            cursor="hand2",
        )
        cross.bind("<Button-1>", lambda event: self.search_var.set(""))

        def updateHint(*args):
            """Show the hint while the box is empty, and the cross when it isn't."""
            if self.search_var.get():
                hint.place_forget()
                cross.place(relx=1.0, x=-2, rely=0.5, anchor="e")
            else:
                cross.place_forget()
                hint.place(x=2, y=0, relheight=1)

        self.search_var.trace_add("write", updateHint)
        updateHint()

    def createMenu(self, parent):
        """Build the row of pill buttons, one for each menu option."""
        bar = tk.Frame(parent)
        bar.pack(fill="x", padx=34, pady=(18, 0))

        options = [
            ("View all", self.viewAll),
            ("Individual", self.viewIndividual),
            ("Highest", self.showHighest),
            ("Lowest", self.showLowest),
            ("Sort", self.showSorted),
            ("Add", self.addStudent),
            ("Delete", self.deleteStudent),
            ("Update", self.updateStudent),
            ("Undo", self.undoLast),
        ]
        self.view_names = [text for text, _ in options[:5]]
        self.menu_buttons = {}

        for text, handler in options:
            quiet = text == "Undo"  # Undo is drawn fainter than the others
            button = RoundedButton(
                bar,
                text,
                lambda handler=handler, text=text: self.runOption(handler, text),
                width=len(text) * 8 + 36,
                fill=BG if quiet else CARD,
                text_colour=MUTED if quiet else TEXT,
            )
            button.pack(side="left", padx=(0, 7))
            self.menu_buttons[text] = button

    def createTableArea(self, parent):
        """Build the white card that holds the table: a heading row and the rows."""
        card = Card(
            parent, width=TABLE_CARD_SIZE[0], height=TABLE_CARD_SIZE[1], radius=26
        )
        card.pack(padx=34, pady=(16, 0))

        # The heading row is its own small canvas, so it stays put when the rows scroll
        heads = tk.Canvas(
            card.body,
            width=TABLE_WIDTH,
            height=HEADER_HEIGHT,
            bg=CARD,
            highlightthickness=0,
        )
        heads.pack()
        heads.create_line(
            0, HEADER_HEIGHT - 1, TABLE_WIDTH, HEADER_HEIGHT - 1, fill=BORDER
        )
        self.heading_canvas = heads
        self.heading_items = {}

        left = 0
        for number, (heading, width, alignment) in enumerate(TABLE_COLUMNS):
            tag = f"column{number}"
            heads.create_rectangle(
                left,
                0,
                left + width,
                HEADER_HEIGHT - 2,
                fill=CARD,
                outline="",
                tags=tag,
            )
            x, anchor = self.columnPosition(left, width, alignment)
            self.heading_items[heading] = heads.create_text(
                x,
                HEADER_HEIGHT // 2,
                text=heading,
                anchor=anchor,
                fill=MUTED,
                font=(FONT, 10, "bold"),
                tags=tag,
            )
            heads.tag_bind(
                tag,
                "<Button-1>",
                lambda event, heading=heading: self.sortByColumn(heading),
            )
            heads.tag_bind(tag, "<Enter>", lambda event: heads.config(cursor="hand2"))
            heads.tag_bind(tag, "<Leave>", lambda event: heads.config(cursor=""))
            left += width

        self.rows_canvas = tk.Canvas(
            card.body,
            width=TABLE_WIDTH,
            height=TABLE_ROWS_HEIGHT,
            bg=CARD,
            highlightthickness=0,
            yscrollincrement=ROW_HEIGHT,
        )
        self.rows_canvas.pack()
        self.rows_canvas.bind("<MouseWheel>", self.scrollRows)
        self.rows_canvas.bind("<Motion>", self.highlightRow)
        self.rows_canvas.bind(
            "<Leave>",
            lambda event: self.rows_canvas.itemconfig("hover", state="hidden"),
        )

    def columnPosition(self, left, width, alignment):
        """Work out where the text of a column goes."""
        if alignment == "w":
            return left + 14, "w"
        return left + width // 2, "center"

    def drawRows(self, students):
        """Draw one row for each student: text, a progress bar and a grade chip."""
        canvas = self.rows_canvas
        canvas.delete("all")

        roundedRectangle(
            canvas, 6, 0, TABLE_WIDTH - 6, ROW_HEIGHT - 2, 12, ACCENT_SOFT, "hover"
        )
        canvas.itemconfig("hover", state="hidden")
        self.hover_top = 0

        if not students:
            canvas.create_text(
                TABLE_WIDTH // 2,
                60,
                text="No students to show.",
                fill=MUTED,
                font=(FONT, 12),
            )

        for index, student in enumerate(students):
            top = index * ROW_HEIGHT
            middle = top + ROW_HEIGHT // 2

            edges = []
            left = 0
            for _, width, alignment in TABLE_COLUMNS:
                edges.append((left, width, alignment))
                left += width
            positions = [self.columnPosition(*edge) for edge in edges]
            name_x, number_x, coursework_x, exam_x, percent_x, grade_x = (
                position[0] for position in positions
            )

            canvas.create_text(
                name_x,
                middle,
                text=student.name,
                anchor="w",
                fill=TEXT,
                font=(FONT, 11, "bold"),
            )
            canvas.create_text(
                number_x, middle, text=str(student.code), fill=MUTED, font=(FONT, 11)
            )
            canvas.create_text(
                coursework_x,
                middle,
                text=str(student.coursework_total),
                fill=TEXT,
                font=(FONT, 11),
            )
            canvas.create_text(
                exam_x, middle, text=str(student.exam), fill=TEXT, font=(FONT, 11)
            )

            grade_colour = GRADE_BAR_COLOURS[student.grade]
            bar_left = percent_x - (PROGRESS_WIDTH + 10 + 46) // 2
            roundedRectangle(
                canvas,
                bar_left,
                middle - 3,
                bar_left + PROGRESS_WIDTH,
                middle + 3,
                3,
                BORDER,
                "track",
            )
            filled = max(6, PROGRESS_WIDTH * student.percentage / 100)
            roundedRectangle(
                canvas,
                bar_left,
                middle - 3,
                bar_left + filled,
                middle + 3,
                3,
                grade_colour,
                "fill",
            )
            canvas.create_text(
                bar_left + PROGRESS_WIDTH + 10,
                middle,
                anchor="w",
                text=f"{student.percentage:.1f}%",
                fill=TEXT,
                font=(FONT, 11),
            )

            roundedRectangle(
                canvas,
                grade_x - 16,
                middle - 12,
                grade_x + 16,
                middle + 12,
                12,
                GRADE_COLOURS[student.grade],
                "chip",
            )
            canvas.create_text(
                grade_x,
                middle,
                text=student.grade,
                fill=grade_colour,
                font=(FONT, 11, "bold"),
            )

            canvas.create_line(
                0, top + ROW_HEIGHT, TABLE_WIDTH, top + ROW_HEIGHT, fill=LINE
            )

        height = max(len(students) * ROW_HEIGHT, TABLE_ROWS_HEIGHT)
        canvas.config(scrollregion=(0, 0, TABLE_WIDTH, height))
        canvas.yview_moveto(0)

    def highlightRow(self, event):
        """Move the pale blue bar to the row under the mouse."""
        canvas = self.rows_canvas
        index = int(canvas.canvasy(event.y) // ROW_HEIGHT)

        if 0 <= index < len(self.shown_students):
            top = index * ROW_HEIGHT + 1
            canvas.move("hover", 0, top - self.hover_top)
            self.hover_top = top
            canvas.itemconfig("hover", state="normal")
        else:
            canvas.itemconfig("hover", state="hidden")

    def scrollRows(self, event):
        """Scroll the rows up or down with the mouse wheel."""
        self.rows_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self.highlightRow(event)

    def setActiveButton(self, name):
        """Highlight one menu button in blue (or none, if name is None)."""
        for text, button in self.menu_buttons.items():
            button.setActive(text == name)

    def clearTable(self):
        """Remove every row from the results table."""
        self.rows_canvas.delete("all")
        self.shown_students = []

    def showStudents(self, students, summary=None, keep_sort=False):
        """Display a list of students in the table, with a summary line."""
        self.clearTable()
        self.shown_students = students  # remembered so headings can re-sort them
        if not keep_sort:
            self.sort_column = None
        self.updateHeadings()
        self.drawRows(students)

        if summary is None:
            summary = (
                f"Students in class: {len(students)}    "
                f"Average percentage: {averagePercentage(students):.1f}%"
            )
        self.summary_label.config(text=summary, fg=TEXT)

    def updateHeadings(self):
        """Show an arrow, in blue, on the heading the table is sorted by."""
        for heading, _, _ in TABLE_COLUMNS:
            text = heading
            sorted_here = heading == self.sort_column
            if sorted_here:
                text += "  ▼" if self.sort_descending else "  ▲"
            self.heading_canvas.itemconfig(
                self.heading_items[heading],
                text=text,
                fill=ACCENT if sorted_here else MUTED,
            )

    def sortByColumn(self, heading):
        """Sort the rows now showing by the heading that was clicked."""
        if not self.shown_students:
            return

        key_name, first_descending = COLUMN_SORT[heading]
        if heading == self.sort_column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = heading
            self.sort_descending = first_descending

        ordered = sortStudents(self.shown_students, key_name, self.sort_descending)
        self.showStudents(
            ordered, summary=self.summary_label.cget("text"), keep_sort=True
        )

    def onSearchChange(self, *args):
        """Filter the table every time the search text changes."""
        if self.ignore_search:
            return  # the program cleared the box itself, so don't search

        text = self.search_var.get().strip()
        if not text:
            self.setActiveButton("View all")
            self.viewAll()
            return

        self.setActiveButton(None)

        matches = searchStudents(self.students, text)

        # If a heading sort is active, keep the matches in that order
        keep_sort = self.sort_column is not None
        if keep_sort:
            key_name, _ = COLUMN_SORT[self.sort_column]
            matches = sortStudents(matches, key_name, self.sort_descending)

        if matches:
            summary = f'{len(matches)} of {len(self.students)} students match "{text}".'
        else:
            summary = f'No students match "{text}".'
        self.showStudents(matches, summary=summary, keep_sort=keep_sort)

    def runOption(self, handler, name=None):
        """Clear the search box, then run a menu option."""
        self.ignore_search = True  # changing the text must not trigger a search
        self.search_var.set("")
        self.ignore_search = False

        if name in self.view_names:
            self.setActiveButton(name)
        handler()
        self.updateStats()  # the option may have added, deleted or changed a student

    def openDialog(self, title, subtitle, width):
        """Create a white pop-up window with a heading and a line of help text."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=CARD)
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        body = tk.Frame(dialog, bg=CARD)
        body.pack(padx=30, pady=26)
        tk.Label(body, text=title, font=(FONT, 18, "bold"), bg=CARD, anchor="w").pack(
            fill="x"
        )
        tk.Label(
            body,
            text=subtitle,
            font=(FONT, 10),
            fg=MUTED,
            bg=CARD,
            anchor="w",
            justify="left",
            wraplength=width,
        ).pack(fill="x", pady=(2, 0))
        return dialog, body

    def addDialogButtons(self, body, dialog, confirm, confirm_text, danger=False):
        """Add the Cancel and confirm buttons at the bottom of a pop-up."""
        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x", pady=(22, 0))

        RoundedButton(
            row,
            confirm_text,
            confirm,
            width=130,
            height=42,
            bold=True,
            fill=ERROR if danger else ACCENT,
            hover=ERROR_HOVER if danger else ACCENT_HOVER,
            text_colour=WHITE,
            outline=None,
            background=CARD,
        ).pack(side="right")
        RoundedButton(
            row,
            "Cancel",
            dialog.destroy,
            width=100,
            height=42,
            bold=True,
            fill=BG,
            hover=BORDER,
            text_colour=MUTED,
            outline=None,
            background=CARD,
        ).pack(side="right", padx=(0, 10))

        dialog.bind("<Return>", lambda event: confirm())

    def showDialog(self, dialog):
        """Centre a pop-up over the main window and wait until it is closed."""
        dialog.update_idletasks()
        x = (
            self.root.winfo_rootx()
            + (self.root.winfo_width() - dialog.winfo_reqwidth()) // 2
        )
        y = (
            self.root.winfo_rooty()
            + (self.root.winfo_height() - dialog.winfo_reqheight()) // 3
        )
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

    def chooseStudent(self, title, prompt, button_text="Select", danger=False):
        """Show a pop-up with a search box and a short list, and return the pick."""
        if not self.students:
            return None

        ordered = sorted(self.students, key=lambda student: student.name.lower())
        chosen = None
        shown = []
        selected = 0

        dialog, body = self.openDialog(title, prompt, 380)

        search_var = tk.StringVar()
        box, entry = makeEntry(body, search_var, width=380, fill=BG, background=CARD)
        box.pack(pady=(16, 6))

        # The list has a fixed height, so the pop-up doesn't change size as you type
        list_frame = tk.Frame(body, bg=CARD, height=MAX_CHOICES * 48, width=380)
        list_frame.pack()
        list_frame.pack_propagate(False)
        info = tk.Label(body, text="", font=(FONT, 10), fg=MUTED, bg=CARD, anchor="w")
        info.pack(fill="x", pady=(6, 0))

        def highlight():
            """Colour the selected row blue and the others plain."""
            for position, row in enumerate(list_frame.winfo_children()):
                row.setActive(position == selected)

        def choose(position):
            """A row was clicked: select it."""
            nonlocal selected
            selected = position
            highlight()

        def move(step):
            """The up or down key was pressed: move the selection."""
            nonlocal selected
            if shown:
                selected = (selected + step) % len(shown)
                highlight()

        def refreshList(*args):
            """Rebuild the list from whatever is typed in the search box."""
            nonlocal shown, selected
            for widget in list_frame.winfo_children():
                widget.destroy()

            matches = searchStudents(ordered, search_var.get().strip())
            shown = matches[:MAX_CHOICES]
            selected = 0

            for position, student in enumerate(shown):
                RoundedButton(
                    list_frame,
                    f"{student.name}   ({student.code})",
                    lambda position=position: choose(position),
                    width=380,
                    height=42,
                    align="w",
                    background=CARD,
                ).pack(pady=3)
            highlight()

            if not matches:
                info.config(text="No students match.")
            elif len(matches) > MAX_CHOICES:
                info.config(
                    text=f"Showing {MAX_CHOICES} of {len(matches)}. "
                    "Keep typing to narrow the list."
                )
            else:
                info.config(text="")

        def confirm():
            """Confirm button: remember the selection and close the pop-up."""
            nonlocal chosen
            if shown:
                chosen = shown[selected]
                dialog.destroy()

        entry.bind("<Down>", lambda event: move(1))
        entry.bind("<Up>", lambda event: move(-1))
        search_var.trace_add("write", refreshList)
        refreshList()

        self.addDialogButtons(body, dialog, confirm, button_text, danger)
        entry.focus_set()
        self.showDialog(dialog)

        return chosen

    def chooseSortOrder(self):
        """Show a pop-up asking what to sort by and in which direction."""
        result = None
        choice = {"key": list(SORT_KEYS)[0], "descending": False}

        dialog, body = self.openDialog(
            "Sort records",
            "Choose what to sort by. Ascending means A-Z or low to high.",
            360,
        )

        key_buttons = {}
        direction_buttons = {}

        def refresh():
            """Highlight the chosen sort key and the chosen direction."""
            for key, button in key_buttons.items():
                button.setActive(key == choice["key"])
            direction_buttons[False].setActive(not choice["descending"])
            direction_buttons[True].setActive(choice["descending"])

        def pickKey(key):
            choice["key"] = key
            refresh()

        def pickDirection(descending):
            choice["descending"] = descending
            refresh()

        tk.Frame(body, bg=CARD, height=10).pack()
        for key in SORT_KEYS:
            button = RoundedButton(
                body,
                key,
                lambda key=key: pickKey(key),
                width=360,
                height=42,
                align="w",
                background=CARD,
            )
            button.pack(pady=3)
            key_buttons[key] = button

        row = tk.Frame(body, bg=CARD)
        row.pack(fill="x", pady=(14, 0))
        for text, descending in (("Ascending", False), ("Descending", True)):
            button = RoundedButton(
                row,
                text,
                lambda descending=descending: pickDirection(descending),
                width=174,
                height=42,
                background=CARD,
            )
            button.pack(side="left", padx=(0, 12))
            direction_buttons[descending] = button
        refresh()

        def confirm():
            """Sort button: remember the choices and close the pop-up."""
            nonlocal result
            result = (choice["key"], choice["descending"])
            dialog.destroy()

        self.addDialogButtons(body, dialog, confirm, "Sort")
        self.showDialog(dialog)

        return result

    def askStudentDetails(self, title, student=None):
        """Show a form for entering a student's details."""
        result = None
        # A student keeping their own code must not clash with themselves
        existing_codes = {s.code for s in self.students if s is not student}

        dialog, body = self.openDialog(
            title, "Fill in every field, then press Save.", 430
        )

        initial = {"name": "", "code": "", "m1": "", "m2": "", "m3": "", "exam": ""}
        if student is not None:
            initial = {
                "name": student.name,
                "code": student.code,
                "m1": student.coursework[0],
                "m2": student.coursework[1],
                "m3": student.coursework[2],
                "exam": student.exam,
            }

        entries = {}

        def addRow(fields):
            """Add one row of labelled boxes. fields is (label, key, width) tuples."""
            row = tk.Frame(body, bg=CARD)
            row.pack(fill="x", pady=(14, 0))
            for label, key, width in fields:
                column = tk.Frame(row, bg=CARD)
                column.pack(side="left", padx=(0, 12))
                tk.Label(
                    column,
                    text=label,
                    font=(FONT, 9, "bold"),
                    fg=MUTED,
                    bg=CARD,
                    anchor="w",
                ).pack(fill="x", pady=(0, 4))
                box, entry = makeEntry(
                    column, None, width=width, fill=BG, background=CARD
                )
                box.pack()
                entry.insert(0, str(initial[key]))
                entries[key] = entry

        addRow([("Code (1000-9999)", "code", 140), ("Name", "name", 266)])
        addRow(
            [
                ("Coursework 1 (/20)", "m1", 126),
                ("Coursework 2 (/20)", "m2", 126),
                ("Coursework 3 (/20)", "m3", 126),
            ]
        )
        addRow([("Exam mark (/100)", "exam", 140)])

        error_label = tk.Label(
            body,
            text="",
            font=(FONT, 10),
            fg=ERROR,
            bg=CARD,
            anchor="w",
            justify="left",
            wraplength=430,
        )
        error_label.pack(fill="x", pady=(14, 0))

        def confirm():
            """Save button: validate the form and close it if everything is valid."""
            nonlocal result
            values = {key: entry.get().strip() for key, entry in entries.items()}
            try:
                result = buildStudent(
                    values["code"],
                    values["name"],
                    [values["m1"], values["m2"], values["m3"]],
                    values["exam"],
                    existing_codes,
                )
            except ValueError as error:
                error_label.config(text=str(error))  # stay open so they can fix it
                return
            dialog.destroy()

        self.addDialogButtons(body, dialog, confirm, "Save")
        entries["code"].focus_set()
        self.showDialog(dialog)

        return result

    def viewAll(self):
        """Option 1: show every student record with the class summary."""
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            return
        self.showStudents(self.students)

    def viewIndividual(self):
        """Option 2: let the user pick a student, then show their record."""
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            return

        student = self.chooseStudent(
            "View individual record", "Select a student:", button_text="Show"
        )
        if student is None:
            return

        self.showStudents([student], summary=f"Showing the record for {student.name}.")

    def showExtreme(self, highest):
        """Show the student(s) with the highest or lowest total mark."""
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
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
        """Option 3: show the student with the highest total score."""
        self.showExtreme(highest=True)

    def showLowest(self):
        """Option 4: show the student with the lowest total score."""
        self.showExtreme(highest=False)

    def showSorted(self):
        """Option 5: show every student, sorted as the user chooses."""
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            return

        choice = self.chooseSortOrder()
        if choice is None:
            return

        key_name, descending = choice
        ordered = sortStudents(self.students, key_name, descending)
        direction = "descending" if descending else "ascending"
        self.showStudents(
            ordered,
            summary=(
                f"All {len(ordered)} students sorted by "
                f"{key_name.lower()} ({direction})."
            ),
        )

    def addStudent(self):
        """Option 6: add a new student and save the file."""
        student = self.askStudentDetails("Add a student record")
        if student is None:
            return

        before = list(self.students)  # a copy of the list, so undo can restore it
        self.students.append(student)
        if not saveStudents(DATA_FILE, self.students):
            self.students.remove(student)  # keep memory and file in step
            return
        self.rememberUndo(before)

        self.showStudents(
            [student],
            summary=(
                f"Added {student.name}. "
                f"The class now has {len(self.students)} students."
            ),
        )

    def deleteStudent(self):
        """Option 7: delete a student (after confirmation) and save the file."""
        if not self.students:
            self.summary_label.config(text="No student records to delete.", fg=ERROR)
            return

        student = self.chooseStudent(
            "Delete a student record",
            "Select the student to delete:",
            button_text="Delete",
            danger=True,
        )
        if student is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm delete",
            f"Delete the record for {student.name} ({student.code})?\n"
            "This cannot be undone.",
            icon="warning",
        )
        if not confirmed:
            return

        # Remember the position so the record can be put back if saving fails
        before = list(self.students)
        position = self.students.index(student)
        self.students.remove(student)

        if not saveStudents(DATA_FILE, self.students):
            self.students.insert(position, student)
            return
        self.rememberUndo(before)

        self.clearTable()
        self.summary_label.config(
            text=f"Deleted {student.name}. The class now has "
            f"{len(self.students)} students.",
            fg=TEXT,
        )

    def updateStudent(self):
        """Option 8: edit an existing student's record and save the file."""
        if not self.students:
            self.summary_label.config(text="No student records to update.", fg=ERROR)
            return

        student = self.chooseStudent(
            "Update a student record",
            "Select the student to update:",
            button_text="Edit",
        )
        if student is None:
            return

        updated = self.askStudentDetails(f"Update {student.name}", student=student)
        if updated is None:
            return

        before = list(self.students)
        position = self.students.index(student)
        self.students[position] = updated

        if not saveStudents(DATA_FILE, self.students):
            self.students[position] = student
            return
        self.rememberUndo(before)

        self.showStudents(
            [updated],
            summary=f"Updated the record for {updated.name}.",
        )

    def rememberUndo(self, before):
        """Keep the student list as it was before a change, so it can be undone."""
        self.undo_stack.append(before)
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)

    def undoLast(self):
        """Option 9: put the class back the way it was before the last change."""
        if not self.undo_stack:
            self.summary_label.config(text="Nothing to undo.", fg=MUTED)
            return

        previous = self.undo_stack.pop()
        current = self.students
        self.students = previous

        if not saveStudents(DATA_FILE, self.students):
            self.students = current
            self.undo_stack.append(previous)  # the undo didn't happen, so keep it
            return

        self.showStudents(
            self.students,
            summary=(
                "Last change undone. "
                f"The class now has {len(self.students)} students."
            ),
        )


def main():
    """Create the Tkinter root window and start the event loop."""
    root = tk.Tk()
    StudentManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
