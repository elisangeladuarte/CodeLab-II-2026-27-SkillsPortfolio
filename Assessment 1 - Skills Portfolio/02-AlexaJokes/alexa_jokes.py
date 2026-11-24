import json
import math
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

# Constants
WINDOW_TITLE = "Alexa Tell Me a Joke"
# Width in pixels at which long jokes wrap onto a new line
WRAP_LENGTH = 600
JOKES_FILE = Path(__file__).parent / "randomJokes.txt"
# Favourite jokes are saved here so they are still there next time
FAVOURITES_FILE = Path(__file__).parent / "myFavourites.json"

# Colors
BG = "#0B1220"  # Window background
CARD = "#141C2F"  # Greyed-out button background
ACCENT = "#2BB6F6"  # Buttons and punchline
ACCENT_HOVER = "#5CC8F8"
TEXT = "#E8EEF9"
MUTED = "#8A96B0"
ERROR = "#FF6B7A"
SUCCESS = "#3DDC97"

# Animation timings (in milliseconds)
TYPE_DELAY_MS = 35  # Pause between typed letters
DRUM_ROLL_STEPS = 5  # How many times the drum roll dots change
DRUM_ROLL_DELAY_MS = 300  # Pause between drum roll steps
PULSE_DELAY_MS = 100  # Pause between steps of the ring pulse
THINKING_STEPS = 9  # How many pulse steps before the joke appears

# The Echo ring
RING_SIZE = 110
RING_WIDTHS = [4, 6, 8, 10, 8, 6]  # Ring thickness at each step of the pulse
GLOW = "#17405E"  # Soft outer circle when the ring is "ready"

# Ring styles: mode -> (ring thickness, ring colour, glow colour)
RING_STYLES = {
    "idle": (6, "#24405C", BG),  # Dim, glow hidden (same colour as background)
    "ready": (8, ACCENT_HOVER, GLOW),  # Bright and glowing
}

# Constants
WINDOW_SIZE = "1100x680"

# Size (in pixels) of the main drawing area (ring, joke and button bar)
STAGE_WIDTH = 780
STAGE_HEIGHT = 610

# Colours (kept in one place so the whole look can be changed easily)
BG = "#0A1020"  # Window background
PANEL = "#101830"  # The favourites panel
DOCK = "#0F1730"  # The bar of buttons at the bottom
CARD = "#141E3A"  # Dark pill buttons and rows
CARD_HOVER = "#1C2850"
ACCENT = "#2BB6F6"  # Main button and the punchline
ACCENT_HOVER = "#5CC8F8"
BRIGHT = "#38D0FF"  # The glowing ring
DARK = "#06101F"  # Dark text on the bright button
TEXT = "#E8EEF9"
MUTED = "#8A96B0"
OFF = "#55607A"  # Text on a disabled button
ERROR = "#FF6B7A"
SUCCESS = "#3DDC97"
STAR = "#F5B83D"
BUBBLE_EDGE = "#4F6FE8"  # Outline of the joke bubble
BUBBLE_FILL = "#0F1730"
WAVE_1 = "#0C1530"  # The two soft waves in the background
WAVE_2 = "#0B1228"

# Fonts
FONT = "Segoe UI"  # Falls back to a default font if it isn't installed
MONO = "Consolas"  # The joke text looks like it is being typed

# Animation timings (in milliseconds)
TYPE_DELAY_MS = 35  # Pause between typed letters
DRUM_ROLL_STEPS = 6  # How many times the drum roll changes
DRUM_ROLL_DELAY_MS = 300  # Pause between drum roll steps
PULSE_DELAY_MS = 120  # Pause between steps of the ring pulse
THINKING_STEPS = 10  # How many pulse steps before the joke appears

# The mic ring (drawn on the stage canvas)
RING_X = STAGE_WIDTH // 2  # Centre of the ring
RING_Y = 112
RING_RADIUS = 80
RING_WIDTHS = [8, 11, 14, 11]  # Ring thickness at each step of the pulse
GLOW_CIRCLES = [(104, "#0E1F3A"), (98, "#10294A"), (92, "#133559")]  # (radius, colour)
ARC_RADII = [96, 112, 128]  # The sound waves on each side of the ring

# Ring styles: mode -> (ring colour, glow visible?, colours of the three sound waves)
RING_STYLES = {
    "idle": ("#1F3A5A", False, ["#16304A", "#122740", "#0F2036"]),
    "ready": (BRIGHT, True, ["#2AA8E6", "#1C6E9E", "#134666"]),
}

# The joke bubble: left, top, right, bottom
BUBBLE = (70, 276, 710, 416)
BUBBLE_TEXT_WIDTH = 576  # Long jokes wrap at this width

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
        radius=30,
        fill=ACCENT,
        hover=ACCENT_HOVER,
        text_colour=DARK,
        background=BG,
        play_icon=False,
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

        text_x = width // 2
        if play_icon:
            # A dark circle with a small triangle on the left of the button
            size = height - 12
            middle = height // 2
            centre = 6 + size // 2
            self.create_oval(6, 6, 6 + size, 6 + size, fill=DARK, outline="")
            self.create_polygon(
                centre - 4,
                middle - 8,
                centre - 4,
                middle + 8,
                centre + 9,
                middle,
                fill=ACCENT,
                outline="",
            )
            text_x = (
                6 + size + width
            ) // 2  # Centre the text in the space that is left

        self.label = self.create_text(
            text_x,
            height // 2,
            text=text,
            fill=text_colour,
            font=(FONT, 12, "bold"),
        )

        self.bind("<Enter>", lambda event: self.setHover(True))
        self.bind("<Leave>", lambda event: self.setHover(False))
        self.bind("<Button-1>", self.click)

    def setHover(self, inside):

        if self.enabled:
            self.itemconfig("shape", fill=self.hover if inside else self.fill)

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
            self.itemconfig("shape", fill=CARD)
            self.itemconfig(self.label, fill=OFF)
            self.config(cursor="arrow")


class Card(tk.Canvas):

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


def makeEntry(parent, variable, width, background, fill, size=13, height=46):

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
    entry.pack(fill="both", expand=True, padx=12)
    return box, entry


def loadFavourites():
    try:
        with open(FAVOURITES_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    favourites = []
    if isinstance(saved, list):
        for item in saved:
            # Each joke was saved as [setup, punchline]
            if isinstance(item, list) and len(item) == 2:
                favourites.append((str(item[0]), str(item[1])))
    return favourites


class RoundedButton(tk.Canvas):

    def __init__(
        self,
        parent,
        text,
        command,
        width=200,
        height=46,
        radius=30,
        fill=ACCENT,
        hover=ACCENT_HOVER,
        text_colour=DARK,
        background=BG,
        play_icon=False,
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

        text_x = width // 2
        if play_icon:
            # A dark circle with a small triangle on the left of the button
            size = height - 12
            middle = height // 2
            centre = 6 + size // 2
            self.create_oval(6, 6, 6 + size, 6 + size, fill=DARK, outline="")
            self.create_polygon(
                centre - 4,
                middle - 8,
                centre - 4,
                middle + 8,
                centre + 9,
                middle,
                fill=ACCENT,
                outline="",
            )
            text_x = (
                6 + size + width
            ) // 2  # centre the text in the space that is left

        self.label = self.create_text(
            text_x,
            height // 2,
            text=text,
            fill=text_colour,
            font=(FONT, 12, "bold"),
        )

        self.bind("<Enter>", lambda event: self.setHover(True))
        self.bind("<Leave>", lambda event: self.setHover(False))
        self.bind("<Button-1>", self.click)

    def setHover(self, inside):

        if self.enabled:
            self.itemconfig("shape", fill=self.hover if inside else self.fill)

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
            self.itemconfig("shape", fill=CARD)
            self.itemconfig(self.label, fill=OFF)
            self.config(cursor="arrow")


class Card(tk.Canvas):

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


def makeEntry(parent, variable, width, background, fill, size=13, height=46):

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
    entry.pack(fill="both", expand=True, padx=12)
    return box, entry


def saveFavourites(favourites):
    try:
        with open(FAVOURITES_FILE, "w", encoding="utf-8") as file:
            json.dump(favourites, file, indent=2)  # Tuples are saved as lists
    except OSError:
        return False
    return True


def findJokes(jokes, word):
    word = word.lower()
    return [
        joke for joke in jokes if word in joke[0].lower() or word in joke[1].lower()
    ]


class JokeAssistant:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.setupStyle()

        # Joke state
        self.jokes = self.loadJokes()  # List of (setup, punchline) tuples
        self.current_joke = None  # The (setup, punchline) tuple on screen
        self.joke_queue = []  # Shuffled jokes still to be told
        self.jokes_told = 0  # Counter shown to the user
        self.anim_job = None  # The pending root.after call, so we cancel it
        self.favourites = loadFavourites()  # Saved (setup, punchline) tuples
        self.after_message = ("", MUTED)  # A message to show once the joke stats

        self.createWidgets()

        # Keyboard shortcuts
        self.root.bind("<Return>", lambda event: self.tellJoke())
        self.root.bind("<Escape>", lambda event: self.quitApp())

    def setupStyle(self):
        self.root.configure(bg=BG)

        # Default colours for every Label and Frame created from now on
        self.root.option_add("*Label.background", BG)
        self.root.option_add("*Label.foreground", TEXT)
        self.root.option_add("*Frame.background", BG)

        # "clam" is a ttk theme that lets us colour buttons on every system
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TButton",
            background=ACCENT,
            foreground=BG,
            font=("Arial", 12),
            padding=8,
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", ACCENT_HOVER), ("disabled", CARD)],
            foreground=[("disabled", MUTED)],
        )

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

    def parseJoke(self, line):
        line = line.strip()

        # Remove a leading "- " list marker if the file has one
        if line.startswith("- "):
            line = line[2:]

        # Skip blank lines and lines with no question mark
        if "?" not in line:
            return None

        # Split on the FIRST "?" only, so a "?" inside the punchline is kept
        setup, punchline = line.split("?", 1)
        setup = setup.strip() + "?"  # Put the question mark back
        punchline = punchline.strip()

        # A line ending in "?" with nothing after it has no punchline
        if not punchline:
            return None

        return setup, punchline

    def loadJokes(self):
        jokes = []
        try:
            with open(JOKES_FILE, "r", encoding="utf-8") as file:
                for line in file:
                    joke = self.parseJoke(line)
                    if joke is not None:
                        jokes.append(joke)
        except FileNotFoundError:
            messagebox.showerror(
                "File not found",
                f"Could not find the jokes file:\n{JOKES_FILE}",
            )
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror(
                "Error reading jokes", f"The jokes file could not be read:\n{error}"
            )
        return jokes

    def createWidgets(self):

        self.createHeader(self.root)

        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=25, pady=(8, 0))

        main = tk.Frame(body)  # ring, joke and buttons
        main.pack(side="left", anchor="n")
        side = tk.Frame(body)  # favourites
        side.pack(side="right", anchor="n", pady=(30, 0))

        self.createStage(main)
        self.createDock(self.stage)
        self.createFavouritesPanel(side)

        # Start with a dim ring and nothing to save or repeat yet
        self.setRing("idle")
        self.setDots(0)
        self.setStatus("Ask me for a joke")
        self.save_button.setEnabled(False)
        self.next_button.setEnabled(False)

        # Without any jokes the buttons can't do anything, so switch them off
        if not self.jokes:
            self.joke_button.setEnabled(False)
            self.search_entry.config(state="disabled")
            self.setStatus("No jokes available.", ERROR)

    def createFavouritesPanel(self, parent):

        card = Card(parent, width=270, height=430, radius=26, fill=PANEL)
        card.pack()
        body = card.body

        title = tk.Frame(body, bg=PANEL)
        title.pack(fill="x", padx=8, pady=(6, 0))
        tk.Label(title, text="\u2605", font=(FONT, 16), fg=STAR, bg=PANEL).pack(
            side="left"
        )
        tk.Label(title, text="Your Favourites", font=(FONT, 14, "bold"), bg=PANEL).pack(
            side="left", padx=8
        )

        # A canvas holds the rows so the list can scroll with the mouse wheel
        self.fav_canvas = tk.Canvas(
            body, width=236, height=290, bg=PANEL, highlightthickness=0
        )
        self.fav_canvas.pack(pady=(10, 0))
        self.fav_rows = tk.Frame(self.fav_canvas, bg=PANEL)
        self.fav_canvas.create_window(0, 0, window=self.fav_rows, anchor="nw")
        self.bindScroll(self.fav_canvas)

        RoundedButton(
            body,
            "Clear All",
            self.clearFavourites,
            width=190,
            height=40,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
            background=PANEL,
        ).pack(pady=(10, 0))

        self.refreshFavourites()

    # New stage (ring, joke bubble, drum)

    def createStage(self, parent):

        stage = tk.Canvas(
            parent,
            width=STAGE_WIDTH,
            height=STAGE_HEIGHT,
            bg=BG,
            highlightthickness=0,
        )
        stage.pack()
        self.stage = stage

        # Two soft waves behind everything
        stage.create_polygon(self.wavePoints(150, 26, 0.0), fill=WAVE_1, outline="")
        stage.create_polygon(self.wavePoints(250, 20, 2.0), fill=WAVE_2, outline="")

        self.drawRing()

        # Text under the ring and the four dots that fill in while "thinking"
        self.status_text = stage.create_text(
            RING_X, 232, text="", fill=MUTED, font=(FONT, 14, "italic")
        )
        self.dot_items = []
        for number in range(4):
            x = RING_X - 33 + number * 22
            self.dot_items.append(
                stage.create_oval(x - 5, 251, x + 5, 261, fill="#1E3350", outline="")
            )

        self.drawBubble()
        self.drawDrum()

        # The Show Punchline button sits where the drum roll will appear
        self.punch_button = RoundedButton(
            stage,
            "Show Punchline",
            self.showPunchline,
            width=170,
            height=42,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
            background=WAVE_2,
        )
        self.punch_window = stage.create_window(
            RING_X, 452, window=self.punch_button, state="hidden"
        )

        self.counter_text = stage.create_text(
            24,
            484,
            anchor="w",
            text="Jokes told: 0",
            fill=MUTED,
            font=(FONT, 10),
        )

    def wavePoints(self, base, height, shift):

        points = []
        for x in range(0, STAGE_WIDTH + 1, 10):
            points += [x, base + height * math.sin(x / 130 + shift)]

        # Close the shape along the bottom edge of the canvas
        points += [STAGE_WIDTH, STAGE_HEIGHT, 0, STAGE_HEIGHT]
        return points

    def drawRing(self):

        stage = self.stage
        x, y = RING_X, RING_Y

        # Soft glow: three circles that get brighter towards the middle
        self.glow_items = []
        for radius, colour in GLOW_CIRCLES:
            self.glow_items.append(
                stage.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill=colour,
                    outline="",
                )
            )

        # Sound waves: a short arc on the left and one on the right, three times
        self.arc_items = []
        for radius in ARC_RADII:
            box = (x - radius, y - radius, x + radius, y + radius)
            left = stage.create_arc(*box, start=150, extent=60, style="arc", width=5)
            right = stage.create_arc(*box, start=-30, extent=60, style="arc", width=5)
            self.arc_items.append((left, right))

        # The ring itself: a dark disc with a thick outline
        self.ring = stage.create_oval(
            x - RING_RADIUS,
            y - RING_RADIUS,
            x + RING_RADIUS,
            y + RING_RADIUS,
            fill="#09101F",
            width=10,
        )

        # The microphone: a pill, a cradle, a stem and a base
        mic = "#EAF2FF"
        roundedRectangle(stage, x - 12, y - 32, x + 12, y + 10, 12, mic, "mic")
        stage.create_arc(
            x - 22,
            y - 22,
            x + 22,
            y + 22,
            start=180,
            extent=180,
            style="arc",
            outline=mic,
            width=4,
        )
        stage.create_line(x, y + 22, x, y + 34, fill=mic, width=4)
        stage.create_line(
            x - 12, y + 34, x + 12, y + 34, fill=mic, width=4, capstyle="round"
        )

    def drawBubble(self):

        stage = self.stage
        left, top, right, bottom = BUBBLE

        # A bubble with an outline: a bigger blue shape with a darker one on top
        roundedRectangle(stage, left, top, right, bottom, 30, BUBBLE_EDGE, "bubble")
        roundedRectangle(
            stage, left + 2, top + 2, right - 2, bottom - 2, 28, BUBBLE_FILL, "bubble"
        )

        # Three small spark lines at the top left corner
        sparks = [(-34, 28, -20, 34), (-28, 14, -18, 24), (-14, 10, -12, 20)]
        for x1, y1, x2, y2 in sparks:
            stage.create_line(
                left + x1,
                top + y1,
                left + x2,
                top + y2,
                fill=ACCENT,
                width=3,
                capstyle="round",
                tags="bubble",
            )

        # The setup, and the punchline which is moved below it when it appears
        self.setup_text = stage.create_text(
            left + 32,
            top + 20,
            anchor="nw",
            text="",
            fill=TEXT,
            font=(MONO, 17),
            width=BUBBLE_TEXT_WIDTH,
            tags="bubble",
        )
        self.punchline_text = stage.create_text(
            left + 32,
            top + 70,
            anchor="nw",
            text="",
            fill=ACCENT,
            font=(MONO, 17),
            width=BUBBLE_TEXT_WIDTH,
            tags="bubble",
        )
        stage.itemconfig("bubble", state="hidden")

    def drawDrum(self):

        stage = self.stage
        x, y = RING_X, 446

        # Bottom edge, body and the top skin, drawn from back to front
        stage.create_oval(
            x - 26, y + 4, x + 26, y + 24, fill="#2E3FB0", outline="", tags="drum"
        )
        stage.create_rectangle(
            x - 26, y - 8, x + 26, y + 14, fill="#3B4FD8", outline="", tags="drum"
        )
        stage.create_oval(
            x - 26,
            y - 18,
            x + 26,
            y + 2,
            fill=TEXT,
            outline="#2E3FB0",
            width=2,
            tags="drum",
        )

        # Two drumsticks. moveSticks() swaps their positions to look like hitting
        self.stick_left = stage.create_line(
            0, 0, 0, 0, fill=STAR, width=4, capstyle="round", tags="drum"
        )
        self.stick_right = stage.create_line(
            0, 0, 0, 0, fill=STAR, width=4, capstyle="round", tags="drum"
        )
        self.moveSticks(True)

        self.drum_text = stage.create_text(
            x,
            484,
            text="* Drum roll *",
            fill=MUTED,
            font=(FONT, 12, "italic"),
            tags="drum",
        )
        stage.itemconfig("drum", state="hidden")

    def moveSticks(self, left_up):
        x, y = RING_X, 446
        high_left = (x - 34, y - 46, x - 10, y - 20)
        low_left = (x - 34, y - 34, x - 10, y - 16)
        high_right = (x + 34, y - 46, x + 10, y - 20)
        low_right = (x + 34, y - 34, x + 10, y - 16)

        self.stage.coords(self.stick_left, *(high_left if left_up else low_left))
        self.stage.coords(self.stick_right, *(low_right if left_up else high_right))

    def setDots(self, count):
        for number, dot in enumerate(self.dot_items):
            self.stage.itemconfig(dot, fill=ACCENT if number < count else "#1E3350")

    def setStatus(self, text, colour=MUTED):
        self.stage.itemconfig(self.status_text, text=text, fill=colour)

    def createHeader(self, parent):

        header = tk.Frame(parent)
        header.pack(fill="x", padx=36, pady=(22, 0))

        logo = tk.Canvas(header, width=34, height=34, bg=BG, highlightthickness=0)
        logo.create_oval(4, 4, 30, 30, outline=ACCENT, width=5)
        logo.pack(side="left")

        tk.Label(header, text="alexa", font=(FONT, 22)).pack(side="left", padx=(10, 14))

        divider = tk.Frame(header, width=1, height=26, bg="#34405E")
        divider.pack(side="left")

        tk.Label(
            header, text="Tell Me a Joke", font=(FONT, 14, "italic"), fg=MUTED
        ).pack(side="left", padx=14)

        RoundedButton(
            header,
            "Quit",
            self.quitApp,
            width=90,
            height=38,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
        ).pack(side="right")

    def createDock(self, stage):

        # background=WAVE_2 is the colour of the wave behind the bar
        dock = Card(
            stage, width=740, height=84, radius=42, fill=DOCK, background=WAVE_2
        )
        stage.create_window(STAGE_WIDTH // 2, STAGE_HEIGHT - 68, window=dock)
        body = dock.body

        # Dark pill buttons share the same options, so keep them in one dictionary
        quiet = dict(
            height=52,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
            background=DOCK,
        )

        self.save_button = RoundedButton(
            body, "\u2665  Save", self.addFavourite, width=110, **quiet
        )
        self.save_button.pack(side="left", padx=3)

        self.joke_button = RoundedButton(
            body,
            "Alexa tell me a Joke",
            self.tellJoke,
            width=262,
            height=52,
            background=DOCK,
            play_icon=True,
        )
        self.joke_button.pack(side="left", padx=3)

        self.next_button = RoundedButton(
            body, "Next Joke", self.tellJoke, width=120, **quiet
        )
        self.next_button.pack(side="left", padx=3)

        # Search: type a word and press Enter
        box, self.search_entry = makeEntry(
            body, None, width=190, size=12, height=52, background=DOCK, fill=CARD
        )
        box.pack(side="left", padx=3)
        self.search_entry.bind("<Return>", self.onSearchEnter)

        # Grey hint text that sits on top of the empty search box
        hint = tk.Label(
            self.search_entry,
            text="Search jokes...",
            font=(FONT, 12),
            fg=MUTED,
            bg=CARD,
        )
        hint.bind("<Button-1>", lambda event: self.search_entry.focus_set())

        def updateHint(event=None):

            if self.search_entry.get():
                hint.place_forget()
            else:
                hint.place(x=2, y=0, relheight=1)

        self.search_entry.bind("<KeyRelease>", updateHint)
        updateHint()

    def pickJoke(self, previous_joke=None):
        if not self.joke_queue:
            self.joke_queue = self.jokes.copy()
            random.shuffle(self.joke_queue)

            # Avoid telling the same joke twice in a row across two rounds
            if len(self.joke_queue) > 1 and self.joke_queue[-1] == self.current_joke:
                self.joke_queue[0], self.joke_queue[-1] = (
                    self.joke_queue[-1],
                    self.joke_queue[0],
                )

        return self.joke_queue.pop()

    def tellJoke(self):
        if not self.jokes:
            return  # Nothing to tell (also protects the Enter shortcut)

        self.startJoke(self.pickJoke())

    def startJoke(self, joke):

        self.cancelAnimations()  # Stop any typing or drum roll still running

        self.current_joke = joke
        self.jokes_told += 1
        self.after_message = ("", MUTED)

        # Show an empty bubble and hide the previous punchline, drum and button
        self.stage.itemconfig("bubble", state="normal")
        self.stage.itemconfig(self.setup_text, text="")
        self.stage.itemconfig(self.punchline_text, text="")
        self.stage.itemconfig("drum", state="hidden")
        self.stage.itemconfig(self.punch_window, state="hidden")
        self.stage.itemconfig(self.counter_text, text=f"Jokes told: {self.jokes_told}")

        self.save_button.setEnabled(False)  # Until the setup is typed
        self.next_button.setEnabled(True)

        # The ring pulses while Alexa "thinks", then the setup is typed out
        self.setStatus("Thinking...")
        self.pulseRing(0, self.showSetup)

    def showSetup(self):

        setup, _ = self.current_joke
        self.setStatus(*self.after_message)
        self.typeText(self.setup_text, setup, when_done=self.enablePunchline)

    def enablePunchline(self):

        self.stage.itemconfig(self.punch_window, state="normal")
        self.save_button.setEnabled(True)

    def showPunchline(self):

        if self.current_joke is None:
            return  # No joke on screen, so nothing to reveal

        self.stage.itemconfig(self.punch_window, state="hidden")  # Already revealing
        self.stage.itemconfig("drum", state="normal")
        self.drumRoll(0)

    def typeText(self, label, text, index=0, when_done=None):
        label.config(text=text[:index])

        if index < len(text):
            # Call this same method again shortly, with one more letter
            self.anim_job = self.root.after(
                TYPE_DELAY_MS,
                lambda: self.typeText(label, text, index + 1, when_done),
            )
        else:
            self.anim_job = None
            if when_done is not None:
                when_done()

    def drumRoll(self, step):
        if step < DRUM_ROLL_STEPS:
            dots = "." * (step % 3 + 1)  # Cycles through 1, 2 and 3 dots
            self.punchline_label.config(text=f"Drum roll{dots}", fg=MUTED)
            self.anim_job = self.root.after(
                DRUM_ROLL_DELAY_MS, lambda: self.drumRoll(step + 1)
            )
        else:
            _, punchline = self.current_joke
            self.punchline_label.config(fg=ACCENT)
            self.typeText(self.punchline_label, punchline)

    def setRing(self, mode):

        colour, glow, wave_colours = RING_STYLES[mode]
        self.stage.itemconfig(self.ring, outline=colour, width=10)

        for item in self.glow_items:
            self.stage.itemconfig(item, state="normal" if glow else "hidden")

        for (left, right), wave_colour in zip(self.arc_items, wave_colours):
            self.stage.itemconfig(left, outline=wave_colour)
            self.stage.itemconfig(right, outline=wave_colour)

    def pulseRing(self, step, when_done):
        if step < THINKING_STEPS:
            width = RING_WIDTHS[step % len(RING_WIDTHS)]  # Cycles through the list
            self.ring_canvas.itemconfig(self.ring, width=width, outline=ACCENT)
            self.ring_canvas.itemconfig(self.ring_glow, outline=BG)
            self.anim_job = self.root.after(
                PULSE_DELAY_MS, lambda: self.pulseRing(step + 1, when_done)
            )
        else:
            self.anim_job = None
            self.setRing("ready")
            when_done()

    # Search
    def onSearchEnter(self, event):
        self.searchJoke()
        return "break"  # Stops Enter from also telling a random joke

    def searchJoke(self):

        word = self.search_entry.get().strip()
        if not word:
            self.setStatus("Type a word to search for.")
            return

        matches = findJokes(self.jokes, word)
        if not matches:
            self.setStatus(f'No jokes about "{word}".', ERROR)
            return

        # Avoid telling the joke that is already on screen, if there is a choice
        choices = [joke for joke in matches if joke != self.current_joke] or matches
        self.startJoke(random.choice(choices))

        # startJoke clears the message, so set it again for when the setup appears
        noun = "joke" if len(matches) == 1 else "jokes"
        self.after_message = (f'Found {len(matches)} {noun} about "{word}".', MUTED)

    # Favourites
    def addFavourite(self):

        if self.current_joke is None:
            return

        if self.current_joke in self.favourites:
            self.setStatus("Already in your favourites.")
            return

        self.favourites.append(self.current_joke)
        self.storeFavourites()
        self.setStatus("Saved to your favourites.", SUCCESS)
        self.refreshFavourites()

    def storeFavourites(self):
        if not saveFavourites(self.favourites):
            messagebox.showerror(
                "Save failed", "Your favourites could not be saved to the file."
            )

        self.refreshFavourites()

    def refreshFavourites(self):

        for widget in self.fav_rows.winfo_children():
            widget.destroy()

        if not self.favourites:
            tk.Label(
                self.fav_rows,
                text="No favourites yet.\nPress Save on a joke you like.",
                font=(FONT, 11),
                fg=MUTED,
                bg=PANEL,
                justify="left",
                wraplength=220,
            ).pack(pady=20, padx=8, anchor="w")

        for position, (setup, _) in enumerate(self.favourites):
            self.makeFavouriteRow(position, setup)

        # Tell the canvas how tall the rows are, so scrolling stops at the end
        self.fav_rows.update_idletasks()
        self.fav_canvas.config(scrollregion=self.fav_canvas.bbox("all"))
        self.fav_canvas.yview_moveto(0)

    def makeFavouriteRow(self, position, setup):

        row = Card(
            self.fav_rows, width=232, height=58, radius=20, fill=CARD, background=PANEL
        )
        row.pack(pady=3)

        shortened = setup if len(setup) <= 44 else setup[:41] + "..."
        text = tk.Label(
            row.body,
            text=shortened,
            font=(FONT, 10),
            bg=CARD,
            anchor="w",
            justify="left",
            wraplength=165,
            cursor="hand2",
        )
        text.pack(side="left", padx=(4, 0))
        text.bind("<Button-1>", lambda event: self.tellFavourite(position))

        cross = tk.Label(
            row.body,
            text="\u2715",
            font=(FONT, 11),
            fg=MUTED,
            bg=CARD,
            cursor="hand2",
        )
        cross.pack(side="right", padx=(0, 4))
        cross.bind("<Button-1>", lambda event: self.deleteFavourite(position))
        cross.bind("<Enter>", lambda event: cross.config(fg=ERROR))
        cross.bind("<Leave>", lambda event: cross.config(fg=MUTED))

        for widget in (row, row.body, text, cross):
            self.bindScroll(widget)

    def bindScroll(self, widget):

        widget.bind("<MouseWheel>", self.scrollFavourites)

    def scrollFavourites(self, event):

        self.fav_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def tellFavourite(self, position):

        if position < len(self.favourites):
            self.startJoke(self.favourites[position])

    def deleteFavourite(self, position):

        if position < len(self.favourites):
            del self.favourites[position]
            self.storeFavourites()
            self.refreshFavourites()

    def clearFavourites(self):

        if not self.favourites:
            return

        if messagebox.askyesno("Clear all", "Delete all of your favourite jokes?"):
            self.favourites = []
            self.storeFavourites()
            self.refreshFavourites()

    def cancelAnimations(self):
        if self.anim_job is not None:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None

    def quitApp(self):
        self.cancelAnimations()
        self.root.destroy()


def main():
    root = tk.Tk()
    JokeAssistant(root)
    preview = tk.Toplevel(root)
    preview.configure(bg=BG)
    app.createHeader(preview)
    app.createStage(preview)
    app.createDock(app.stage)
    app.save_button.setEnabled(False)
    app.next_button.setEnabled(False)
    RoundedButton(root, "Test", lambda: print("clicked")).pack(pady=10)
    RoundedButton(
        root, "Alexa tell me a Joke", lambda: None, width=262, height=52, play_icon=True
    ).pack(pady=10)
    root.mainloop()


if __name__ == "__main__":
    main()
