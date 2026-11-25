import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

# Constants
WINDOW_TITLE = "Student Manager"
WINDOW_SIZE = "1100x660"
# Build the path from this script's location so it works from any folder
DATA_FILE = Path(__file__).parent / "studentMarks.txt"
# Maximum marks available (3 coursework marks of 20, plus an exam out of 100)
MAX_COURSEWORK_MARK = 20
MAX_EXAM_MARK = 100
COURSEWORK_COUNT = 3
MAX_TOTAL = COURSEWORK_COUNT * MAX_COURSEWORK_MARK + MAX_EXAM_MARK  # 160
# Valid range for a student code, and the number of comma-separated fields
MIN_CODE = 1000
MAX_CODE = 9999
FIELDS_PER_LINE = COURSEWORK_COUNT + 3
# Maximum number of file problems listed in the warning popup
MAX_PROBLEMS_SHOWN = 5
# How many changes can be undone
MAX_UNDO = 10
# Grade boundaries: minimum percentage, grade, checked from highest to lowest
GRADE_BOUNDARIES = [(70, "A"), (60, "B"), (50, "C"), (40, "D"), (0, "F")]
# Table columns: (heading, width in pixels, text alignment)
TABLE_COLUMNS = [
    ("Name", 200, "w"),
    ("Number", 80, "center"),
    ("Coursework (/60)", 140, "center"),
    ("Exam (/100)", 100, "center"),
    ("Percentage", 100, "center"),
    ("Grade", 70, "center"),
]
# Colours (kept in one place so the whole look can be changed easily)
BG = "#F3F5F9"  # Window background (a very pale grey-blue)
CARD = "#FFFFFF"  # White cards, table and entry boxes
BORDER = "#E1E6EE"  # Thin outlines and dividers
LINE = "#EDF0F5"  # The faint line between table rows
ACCENT = "#2563EB"  # The main blue
ACCENT_HOVER = "#1D4ED8"
ACCENT_SOFT = "#EFF4FF"  # Pale blue for a selected row or option
TEXT = "#1B2A41"  # Dark navy text
MUTED = "#6B7A90"  # Secondary text
ERROR = "#DC2626"
SUCCESS = "#16A34A"
OFF = "#A5B0C0"  # Text on a disabled button
WHITE = "#FFFFFF"  # Text on blue buttons

# Pale background for each grade (used for the grade chip in the table)
GRADE_COLOURS = {
    "A": "#DCFCE7",
    "B": "#DBEAFE",
    "C": "#FEF3C7",
    "D": "#FFEDD5",
    "F": "#FEE2E2",
}

# Strong colour for each grade (the chip letter, the chart bars and progress bars)
GRADE_BAR_COLOURS = {
    "A": "#16A34A",
    "B": "#2563EB",
    "C": "#D97706",
    "D": "#EA580C",
    "F": "#DC2626",
}

# Font
FONT = "Segoe UI"
FONT_LIGHT = "Segoe UI Light"

# Sizes of the cards in the top row (they add up to the 1032 pixels between
# The window's left and right margins: 3 cards + 3 gaps of 16 + the chart card)
STAT_WIDTH = 230
STAT_HEIGHT = 128
CHART_CARD_WIDTH = 294
CHART_SIZE = (276, 110)  # The chart canvas, a little smaller than its card

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
    "Coursework (/60)": ("Coursework total", True),
    "Exam (/100)": ("Exam mark", True),
    "Percentage": ("Overall percentage", True),
    "Grade": (
        "Overall percentage",
        True,
    ),  # Grades follow the percentage, so A is first
}

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


def drawOutlinedShape(canvas, width, height, radius, fill, edge):

    roundedRectangle(canvas, 0, 0, width, height, radius, edge, "edge")
    roundedRectangle(canvas, 1, 1, width - 1, height - 1, radius - 1, fill, "shape")


class RoundedButton(tk.Canvas):

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
        self.label = self.create_text(
            width // 2,
            height // 2,
            text=text,
            fill=text_colour,
            font=(FONT, 11, "bold" if bold else "normal"),
        )

        self.bind("<Enter>", lambda event: self.refresh(True))
        self.bind("<Leave>", lambda event: self.refresh(False))
        self.bind("<Button-1>", self.click)

    def paint(self, fill, edge, text):

        self.itemconfig("shape", fill=fill)
        self.itemconfig("edge", fill=edge)
        self.itemconfig(self.label, fill=text)

    def refresh(self, hovering=False):

        if not self.enabled:
            self.paint(self.background, BORDER, OFF)
        elif self.active:
            colour = ACCENT_HOVER if hovering else ACCENT
            self.paint(colour, colour, WHITE)
        else:
            inside = self.hover if hovering else self.fill
            self.paint(inside, self.outline or inside, self.text_colour)

    def click(self, event):

        if self.enabled:
            self.command()

    def setEnabled(self, enabled):

        self.enabled = enabled
        self.config(cursor="hand2" if enabled else "arrow")
        self.refresh()

    def setActive(self, active):

        self.active = active
        self.refresh()


class Card(tk.Canvas):

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
        # The edge to stay clear of the rounded corners (bigger radius = bigger gap)
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

        self.itemconfig("edge", fill=colour)


def makeEntry(parent, variable, width, height=42, size=12, fill=CARD, background=BG):

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

    def __init__(self, code, name, coursework, exam):
        self.code = code
        self.name = name
        self.coursework = coursework
        self.exam = exam
        # Earlier versions of the student list, newest last, for the undo option
        self.undo_stack = []

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
        return (
            f"{self.code} {self.name}: {self.total}/{MAX_TOTAL} "
            f"({self.percentage:.1f}%) grade {self.grade}"
        )


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

    # The first three marks are coursework, the last one is the exam
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

    # Cross-check the count on the first line against what was loaded
    if expected_count is not None and expected_count != len(students):
        problems.append(
            f"The file says {expected_count} students but "
            f"{len(students)} valid records were loaded."
        )

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


def countGrades(students):
    counts = {grade: 0 for _, grade in GRADE_BOUNDARIES}
    for student in students:
        counts[student.grade] += 1
    return counts


def searchStudents(students, text):
    text = text.lower()
    return [
        student
        for student in students
        if text in student.name.lower() or text in str(student.code)
    ]


class StudentManager:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(1000, 800)
        self.setupStyle()

        # Student records
        self.students, problems = loadStudents(DATA_FILE)
        if problems:
            self.reportProblems(problems)

        # The search box text. The trace runs onSearchChange on every keystroke.
        self.search_var = tk.StringVar()
        self.ignore_search = False  # True while the program itself changes the text
        self.search_var.trace_add("write", self.onSearchChange)

        self.createWidgets()

        # What the table is showing, and which heading it is sorted by
        self.shown_students = []
        self.sort_column = None
        self.sort_descending = False

        self.placeholder = tk.Label(
            self.root, text="Student Manager", font=("Arial", 24, "bold")
        )
        self.placeholder.grid(row=0, column=0, pady=200)

    def setupStyle(self):
        self.root.configure(bg=BG)

        # Default colours for plain Tkinter widgets created from now on
        defaults = {
            "*Font": f"{{{FONT}}} 11",
            "*Label.background": BG,
            "*Label.foreground": TEXT,
            "*Frame.background": BG,
            "*Toplevel.background": BG,
            "*Entry.background": CARD,
            "*Entry.foreground": TEXT,
            "*Entry.insertBackground": TEXT,
            "*Entry.relief": "flat",
            "*Entry.highlightThickness": 1,
            "*Entry.highlightBackground": BORDER,
            "*Entry.highlightColor": ACCENT,
            "*Radiobutton.background": BG,
            "*Radiobutton.foreground": TEXT,
            "*Radiobutton.activeBackground": BG,
            "*Radiobutton.activeForeground": TEXT,
            "*Radiobutton.selectColor": CARD,
            "*Radiobutton.highlightThickness": 0,
            # The drop-down list that opens from a Combobox
            "*TCombobox*Listbox.background": CARD,
            "*TCombobox*Listbox.foreground": TEXT,
            "*TCombobox*Listbox.selectBackground": ACCENT,
            "*TCombobox*Listbox.selectForeground": WHITE,
        }
        for pattern, value in defaults.items():
            self.root.option_add(pattern, value)

        # "clam" is a ttk theme that lets us colour widgets on every system
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TButton",
            background=ACCENT,
            foreground=BG,
            font=("Arial", 11),
            padding=8,
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", ACCENT_HOVER), ("disabled", CARD)],
            foreground=[("disabled", MUTED)],
        )

        # The menu buttons: dark, left-aligned, and teal when the mouse is over them
        style.configure(
            "Menu.TButton",
            background=CARD,
            foreground=TEXT,
            anchor="w",
            padding=(14, 8),
        )
        style.map(
            "Menu.TButton",
            background=[("active", ACCENT)],
            foreground=[("active", WHITE)],
        )

        style.configure(
            "TCombobox",
            fieldbackground=CARD,
            background=CARD,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=CARD,
            darkcolor=CARD,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", CARD)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", CARD)],
            selectforeground=[("readonly", TEXT)],
        )

        # The results table
        style.configure(
            "Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=28,
            borderwidth=0,
            font=("Arial", 11),
            bordercolor=BG,
            lightcolor=BG,
            darkcolor=BG,
        )
        style.map(
            "Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", WHITE)],
        )
        style.configure(
            "Treeview.Heading",
            background=BORDER,
            foreground=TEXT,
            font=(FONT, 11, "bold"),
            padding=6,
            borderwidth=0,
        )
        style.map("Treeview.Heading", background=[("active", CARD)])

        style.configure(
            "TScrollbar",
            background=ACCENT,
            troughcolor=CARD,
            arrowcolor=BG,
            bordercolor=CARD,
            lightcolor=ACCENT,
            darkcolor=ACCENT,
        )
        style.map("TScrollbar", background=[("active", ACCENT_HOVER)])

    # Title, stat cards and grade chart

    def createHeader(self, parent):

        self.header = tk.Frame(parent)
        self.header.pack(fill="x", padx=34, pady=(26, 0))

        tk.Label(self.header, text="Student Manager", font=(FONT_LIGHT, 30)).pack(
            side="left"
        )

    def createStats(self, parent):

        row = tk.Frame(parent)
        row.pack(fill="x", padx=34, pady=(18, 0))

        # Each stat card has a small caption, a big number and a line of detail
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

        # The grade chart sits in a card of its own
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

        value, detail = self.stat_labels[key]
        name = matches[0].name
        if len(matches) > 1:
            name += f" +{len(matches) - 1} more"  # a tie
        value.config(text=f"{matches[0].percentage:.1f}%", fg=colour)
        detail.config(text=name)

    def drawGradeChart(self):
        """Draw one rounded bar for each grade, showing how many students got it."""
        canvas = self.grade_chart
        canvas.delete("all")  # Wipe the old chart before drawing the new one
        width, height = CHART_SIZE

        counts = countGrades(self.students)
        biggest = max(max(counts.values()), 1)  # Avoids dividing by zero

        top = 20  # Room for the number above the tallest bar
        baseline = height - 22  # The bars stand on this line, with room for letters
        plot_height = baseline - top
        slot = width / len(counts)  # The width given to each bar
        bar_width = slot * 0.5

        for position, (grade, count) in enumerate(counts.items()):
            left = position * slot + (slot - bar_width) / 2
            centre = left + bar_width / 2

            if count > 0:
                bar_height = max(plot_height * count / biggest, 8)
                colour = GRADE_BAR_COLOURS[grade]
            else:
                bar_height = 3  # A thin pale line, so the grade is still shown
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
        shown = problems[:MAX_PROBLEMS_SHOWN]
        message = "\n".join(shown)
        if len(problems) > MAX_PROBLEMS_SHOWN:
            message += f"\n...and {len(problems) - MAX_PROBLEMS_SHOWN} more."
        messagebox.showwarning("Problems with the data file", message)

    def createWidgets(self):
        # Left column holds the menu, right column holds the results
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Menu
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
            ("7. Delete a student record", self.deleteStudent),
            ("8. Update a student record", self.updateStudent),
            ("9. Undo last change", self.undoLast),
        ]
        for text, handler in menu_options:
            ttk.Button(
                menu_frame,
                text=text,
                width=28,
                style="Menu.TButton",
                command=lambda handler=handler: self.runOption(handler),
            ).pack(pady=3)

        # Grade chart under the menu
        tk.Label(menu_frame, text="GRADES", font=("Arial", 10, "bold"), fg=MUTED).pack(
            pady=(25, 5)
        )
        # The small width lets the menu buttons decide how wide the menu is
        self.chart_canvas = tk.Canvas(
            menu_frame, width=100, height=170, bg=CARD, highlightthickness=0
        )
        self.chart_canvas.pack(fill="x")
        self.chart_canvas.bind("<Configure>", self.drawChart)  # redraw when resized

        # Results area
        display_frame = tk.Frame(self.root, padx=10, pady=15)
        display_frame.grid(row=0, column=1, sticky="nsew")
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(1, weight=1)  # The table takes the spare height

        # Search box above the table: it filters the rows as you type
        search_frame = tk.Frame(display_frame)
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        tk.Label(search_frame, text="Search name or number:").pack(side="left")
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, font=("Arial", 12), width=28
        )
        self.search_entry.pack(side="left", padx=10, ipady=4)
        self.clear_button = ttk.Button(
            search_frame,
            text="Clear",
            width=8,
            command=lambda: self.search_var.set(""),
        )
        self.clear_button.pack(side="left")

        headings = [heading for heading, _, _ in TABLE_COLUMNS]
        self.table = ttk.Treeview(
            display_frame, columns=headings, show="headings", selectmode="browse"
        )
        for heading, width, alignment in TABLE_COLUMNS:
            self.table.heading(
                heading,
                text=heading,
                command=lambda heading=heading: self.sortByColumn(heading),
            )
            self.table.column(heading, width=width, anchor=alignment)
        self.table.grid(row=1, column=0, sticky="nsew")

        # One tag per grade, so each row can be tinted by its grade
        for grade, colour in GRADE_COLOURS.items():
            self.table.tag_configure(grade, background=colour)

        scrollbar = ttk.Scrollbar(
            display_frame, orient="vertical", command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        # Summary
        self.summary_label = tk.Label(
            display_frame,
            text="Choose an option from the menu.",
            font=("Arial", 11),
            anchor="w",
        )
        self.summary_label.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

        # Without any data there is nothing to show
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            self.search_entry.config(state="disabled")
            self.clear_button.config(state="disabled")

    def clearTable(self):
        self.table.delete(*self.table.get_children())
        self.shown_students = []

    def showStudents(self, students, summary=None, keep_sort=False):
        self.clearTable()
        self.shown_students = students  # Remembering so heading can re-sort them
        if not keep_sort:
            self.sort_column = None
        self.updateHeadings()

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
                tags=(student.grade,),  # Picks the row colour from GRADE_COLOURS
            )

        if summary is None:
            summary = (
                f"Students in class: {len(students)}    "
                f"Average percentage: {averagePercentage(students):.1f}%"
            )
        self.summary_label.config(text=summary, fg=TEXT)

    def viewAll(self):
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            return
        self.showStudents(self.students)

    # Chart
    def drawChart(self, event=None):
        canvas = self.chart_canvas
        canvas.delete("all")  # Wipe the old chart before drawing the new one
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        counts = countGrades(self.students)
        biggest = max(counts.values())
        if biggest == 0 or width < 20:
            canvas.create_text(width / 2, height / 2, text="No data", fill=MUTED)
            return

        top = 22  # Room for the number above the tallest bar
        baseline = height - 24  # The bars stand on this line, with room for letters
        plot_height = baseline - top
        slot = width / len(counts)  # The width given to each bar
        bar_width = slot * 0.6

        for position, (grade, count) in enumerate(counts.items()):
            left = position * slot + (slot - bar_width) / 2
            centre = left + bar_width / 2
            bar_height = plot_height * count / biggest

            if count > 0:
                canvas.create_rectangle(
                    left,
                    baseline - bar_height,
                    left + bar_width,
                    baseline,
                    fill=GRADE_BAR_COLOURS[grade],
                    width=0,
                )
            canvas.create_text(
                centre,
                baseline - bar_height - 10,
                text=str(count),
                fill=TEXT,
                font=("Arial", 10, "bold"),
            )
            canvas.create_text(
                centre, height - 11, text=grade, fill=MUTED, font=("Arial", 11, "bold")
            )

    # Search
    def onSearchChange(self, *args):
        if self.ignore_search:
            return  # The program cleared the box itself, so don't search

        text = self.search_var.get().strip()
        if not text:
            self.viewAll()  # An empty box means "show everyone"
            return

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

    def runOption(self, handler):
        self.ignore_search = True  # Changing the text must not trigger a search
        self.search_var.set("")
        self.ignore_search = False
        handler()
        self.drawChart()  # The option may have added, deleted or changed a student

    # Dialogs
    def chooseStudent(self, title, prompt):
        # Alphabetical order makes a long list easier to scan
        if not self.students:
            return None

        ordered = sorted(self.students, key=lambda student: student.name.lower())
        labels = [f"{student.name} ({student.code})" for student in ordered]
        chosen = None

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)  # Keep it on top of the main window
        dialog.resizable(False, False)

        def confirm():
            nonlocal chosen
            index = combo.current()  # -1 if nothing is selected
            if index >= 0:
                chosen = ordered[index]
            dialog.destroy()

        tk.Label(dialog, text=prompt, font=("Arial", 11)).pack(padx=20, pady=(15, 5))

        # State="readonly" stops the user typing something that isn't in the list
        combo = ttk.Combobox(dialog, values=labels, state="readonly", width=35)
        combo.pack(padx=20, pady=5)
        combo.current(0)  # Preselect the first student

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=(10, 15))
        ttk.Button(button_frame, text="OK", width=10, command=confirm).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Cancel", width=10, command=dialog.destroy).pack(
            side="left", padx=5
        )

        dialog.bind("<Return>", lambda event: confirm())
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        # Modal: block the main window until this pop-up is closed
        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

        return chosen

    def viewIndividual(self):
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            return

        student = self.chooseStudent("View individual record", "Select a student:")
        if student is None:
            return  # The user cancelled, so leave the display unchanged

        self.showStudents([student], summary=f"Showing the record for {student.name}.")

    def showExtreme(self, highest):
        """Show the student(s) with the highest or lowest total mark.

        Args:
            highest (bool): True for the highest total, False for the lowest.
        """
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
        self.showExtreme(highest=True)

    def showLowest(self):
        self.showExtreme(highest=False)

    def updateHeadings(self):
        for heading, _, _ in TABLE_COLUMNS:
            text = heading
            if heading == self.sort_column:
                text += (
                    "  \u25bc" if self.sort_descending else "  \u25b2"
                )  # Down / up arrow
            self.table.heading(heading, text=text)

    def sortByColumn(self, heading):
        if not self.shown_students:
            return  # Nothing on screen to sort

        key_name, first_descending = COLUMN_SORT[heading]
        if heading == self.sort_column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = heading
            self.sort_descending = first_descending

        ordered = sortStudents(self.shown_students, key_name, self.sort_descending)
        # Keep the summary text that is already showing
        self.showStudents(
            ordered, summary=self.summary_label.cget("text"), keep_sort=True
        )

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

        tk.Label(dialog, text="Sort by:", font=("Arial", 11)).pack(
            padx=20, pady=(15, 5)
        )
        key_combo = ttk.Combobox(
            dialog, values=list(SORT_KEYS), state="readonly", width=25
        )
        key_combo.pack(padx=20, pady=5)
        key_combo.current(0)

        # Radio buttons share one variable, so only one can be selected
        direction = tk.StringVar(value="ascending")
        tk.Radiobutton(
            dialog,
            text="Ascending (low to high, A-Z)",
            variable=direction,
            value="ascending",
        ).pack(anchor="w", padx=30)
        tk.Radiobutton(
            dialog,
            text="Descending (high to low, Z-A)",
            variable=direction,
            value="descending",
        ).pack(anchor="w", padx=30)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=(10, 15))
        ttk.Button(button_frame, text="OK", width=10, command=confirm).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Cancel", width=10, command=dialog.destroy).pack(
            side="left", padx=5
        )

        dialog.bind("<Return>", lambda event: confirm())
        dialog.bind("<Escape>", lambda event: dialog.destroy())

        dialog.wait_visibility()
        dialog.grab_set()
        self.root.wait_window(dialog)

        return result

    def showSorted(self):
        if not self.students:
            self.summary_label.config(text="No student records loaded.", fg=ERROR)
            return

        choice = self.chooseSortOrder()
        if choice is None:
            return  # Cancelled, so leave the display unchanged

        key_name, descending = choice
        ordered = sortStudents(self.students, key_name, descending)
        direction = "descending" if descending else "ascending"
        self.showStudents(
            ordered,
            summary=f"All {len(ordered)} students sorted by {key_name.lower()} ({direction}).",
        )

    def askStudentDetails(self, title, student=None):
        result = None
        # A student keeping their own code must not clash with themselves
        existing_codes = {s.code for s in self.students if s is not student}

        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.resizable(False, False)

        labels = [
            "Student name",
            "Student code (1000-9999)",
            "Coursework mark 1 (/20)",
            "Coursework mark 2 (/20)",
            "Coursework mark 3 (/20)",
            "Exam mark (/100)",
        ]
        initial = [""] * len(labels)
        if student is not None:
            initial = [
                student.name,
                student.code,
                *student.coursework,
                student.exam,
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

        error_label = tk.Label(dialog, text="", fg=ERROR, wraplength=300)
        error_label.grid(row=len(labels), column=0, columnspan=2, pady=(5, 0))

        def confirm():
            nonlocal result
            name, code, m1, m2, m3, exam = (entry.get().strip() for entry in entries)
            try:
                result = buildStudent(code, name, [m1, m2, m3], exam, existing_codes)
            except ValueError as error:
                error_label.config(text=str(error))  # Stay open so they can fix it
                return
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.grid(row=len(labels) + 1, column=0, columnspan=2, pady=15)
        ttk.Button(button_frame, text="Save", width=10, command=confirm).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Cancel", width=10, command=dialog.destroy).pack(
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
        student = self.askStudentDetails("Add a student record")
        if student is None:
            return  # Cancelled

        before = list(self.students)
        self.students.append(student)
        if not saveStudents(DATA_FILE, self.students):
            self.students.remove(student)  # Keep memory and file in step
            return
        self.rememberUndo(before)

        self.showStudents(
            [student],
            summary=f"Added {student.name}. The class now has {len(self.students)} students.",
        )

    def deleteStudent(self):
        if not self.students:
            self.summary_label.config(text="No student records to delete.", fg=ERROR)
            return

        student = self.chooseStudent(
            "Delete a student record", "Select the student to delete:"
        )
        if student is None:
            return  # Cancelled

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
            self.students.insert(position, student)  # Keep memory and file in step
            return
        self.rememberUndo(before)

        self.clearTable()
        self.summary_label.config(
            text=f"Deleted {student.name}. The class now has "
            f"{len(self.students)} students.",
            fg=TEXT,
        )

    def updateStudent(self):
        if not self.students:
            self.summary_label.config(text="No student records to update.", fg=ERROR)
            return

        student = self.chooseStudent(
            "Update a student record", "Select the student to update:"
        )
        if student is None:
            return  # Cancelled

        # The form is pre-filled, so the user only changes what they need to
        updated = self.askStudentDetails(f"Update {student.name}", student=student)
        if updated is None:
            return  # Cancelled

        # Swap the old record for the new one, keeping its position in the list
        before = list(self.students)
        position = self.students.index(student)
        self.students[position] = updated

        if not saveStudents(DATA_FILE, self.students):
            self.students[position] = student  # Keep memory and file in step
            return
        self.rememberUndo(before)

    def rememberUndo(self, before):
        self.undo_stack.append(before)
        if len(self.undo_stack) > MAX_UNDO:
            self.undo_stack.pop(0)  # forget the oldest change

    def undoLast(self):
        if not self.undo_stack:
            self.summary_label.config(text="Nothing to undo.", fg=MUTED)
            return

        previous = self.undo_stack.pop()
        current = self.students
        self.students = previous

        if not saveStudents(DATA_FILE, self.students):
            self.students = current  # Keep memory and file in step
            self.undo_stack.append(previous)  # The undo didn't happen, so keep it
            return

        self.showStudents(
            self.students,
            summary=(
                "Last change undone. "
                f"The class now has {len(self.students)} students."
            ),
        )


def main():
    root = tk.Tk()
    StudentManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
