# AI acknowledgement: this program was developed with help from Claude
# Prompts used:
# "Redesign the joke assistant so it looks like a voice assistant"
# "Add sound effects (ding, drum roll, rimshot) and a sound on/off button"

import json
import math
import random
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

WINDOW_TITLE = "Alexa Tell Me a Joke"
WINDOW_SIZE = "1100x680"

STAGE_WIDTH = 780
STAGE_HEIGHT = 610

# Build the path from this script's location so it works from any folder
JOKES_FILE = Path(__file__).parent / "randomJokes.txt"

FAVOURITES_FILE = Path(__file__).parent / "myFavourites.json"
SOUNDS_DIR = Path(__file__).parent / "sounds"
sound_on = True

# Colours
BG = "#0A1020"  # window background
PANEL = "#101830"  # the favourites panel
DOCK = "#0F1730"  # the bar of buttons at the bottom
CARD = "#141E3A"  # dark pill buttons and rows
CARD_HOVER = "#1C2850"
ACCENT = "#2BB6F6"  # main button and the punchline
ACCENT_HOVER = "#5CC8F8"
BRIGHT = "#38D0FF"  # the glowing ring
DARK = "#06101F"  # dark text on the bright button
TEXT = "#E8EEF9"
MUTED = "#8A96B0"
OFF = "#55607A"  # text on a disabled button
ERROR = "#FF6B7A"
SUCCESS = "#3DDC97"
STAR = "#F5B83D"
BUBBLE_EDGE = "#4F6FE8"  # outline of the joke bubble
BUBBLE_FILL = "#0F1730"
WAVE_1 = "#0C1530"  # the two soft waves in the background
WAVE_2 = "#0B1228"

FONT = "Segoe UI"  # falls back to a default font if it isn't installed
MONO = "Consolas"  # the joke text looks like it is being typed

# Animation timings (in milliseconds)
TYPE_DELAY_MS = 35  # pause between typed letters
DRUM_ROLL_STEPS = 6  # how many times the drum roll changes
DRUM_ROLL_DELAY_MS = 300  # pause between drum roll steps
PULSE_DELAY_MS = 120  # pause between steps of the ring pulse
THINKING_STEPS = 10  # how many pulse steps before the joke appears

RING_X = STAGE_WIDTH // 2  # centre of the ring
RING_Y = 112
RING_RADIUS = 80
RING_WIDTHS = [8, 11, 14, 11]  # ring thickness at each step of the pulse
GLOW_CIRCLES = [(104, "#0E1F3A"), (98, "#10294A"), (92, "#133559")]  # (radius, colour)
ARC_RADII = [96, 112, 128]  # the sound waves on each side of the ring

# Ring styles: mode -> (ring colour, glow visible?, colours of the three sound waves)
RING_STYLES = {
    "idle": ("#1F3A5A", False, ["#16304A", "#122740", "#0F2036"]),
    "ready": (BRIGHT, True, ["#2AA8E6", "#1C6E9E", "#134666"]),
}

# The joke bubble: left, top, right, bottom
BUBBLE = (70, 276, 710, 416)
BUBBLE_TEXT_WIDTH = 576  # long jokes wrap at this width


player = None  # the sound player process on Mac and Linux, so it can be stopped


def soundLabel():
    """Return the text for the sound button."""
    return "Sound: on" if sound_on else "Sound: off"


def playSound(name):
    """Play a short sound from the sounds folder without freezing the window."""
    global player
    path = SOUNDS_DIR / name
    if not sound_on or not path.exists():
        return

    stopSound()
    try:
        if sys.platform == "win32":
            import winsound

            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == "darwin":
            player = subprocess.Popen(["afplay", str(path)])
        else:
            player = subprocess.Popen(["aplay", "-q", str(path)])
    except (OSError, RuntimeError):
        pass  # a missing sound player must never stop the app


def stopSound():
    """Stop the sound that is playing, if any."""
    global player
    if sys.platform == "win32":
        try:
            import winsound

            winsound.PlaySound(None, winsound.SND_PURGE)
        except RuntimeError:
            pass
    elif player is not None:
        player.terminate()
        player = None


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


class RoundedButton(tk.Canvas):
    """A clickable pill-shaped button, drawn on a canvas."""

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
            text_x = (6 + size + width) // 2

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
        """Change the colour when the mouse enters or leaves the button."""
        if self.enabled:
            self.itemconfig("shape", fill=self.hover if inside else self.fill)

    def click(self, event):
        """Run the button's command (unless the button is disabled)."""
        if self.enabled:
            self.command()

    def setEnabled(self, enabled):
        """Turn the button on or off. A disabled button looks greyed out."""
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


def makeEntry(parent, variable, width, background, fill, size=13, height=46):
    """Create a pill-shaped text box."""
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
    """Read the saved favourite jokes."""
    try:
        with open(FAVOURITES_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    favourites = []
    if isinstance(saved, list):
        for item in saved:
            if isinstance(item, list) and len(item) == 2:
                favourites.append((str(item[0]), str(item[1])))
    return favourites


def saveFavourites(favourites):
    """Write the favourite jokes to the file."""
    try:
        with open(FAVOURITES_FILE, "w", encoding="utf-8") as file:
            json.dump(favourites, file, indent=2)  # tuples are saved as lists
    except OSError:
        return False
    return True


def findJokes(jokes, word):
    """Return the jokes whose setup or punchline contains a word."""
    word = word.lower()
    return [
        joke for joke in jokes if word in joke[0].lower() or word in joke[1].lower()
    ]


class JokeAssistant:
    """Main application class: holds the window and the joke state."""

    def __init__(self, root):
        """Set up the main window and initialise the joke state."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.setupStyle()

        self.jokes = self.loadJokes()
        self.current_joke = None
        self.joke_queue = []
        self.jokes_told = 0
        self.anim_job = None
        self.after_message = ("", MUTED)
        self.favourites = loadFavourites()

        self.createWidgets()

        self.root.bind("<Return>", lambda event: self.tellJoke())
        self.root.bind("<Escape>", lambda event: self.quitApp())

    def setupStyle(self):
        """Apply the dark theme to the window and the labels."""
        self.root.configure(bg=BG)

        self.root.option_add("*Label.background", BG)
        self.root.option_add("*Label.foreground", TEXT)
        self.root.option_add("*Frame.background", BG)

    def parseJoke(self, line):
        """Split one line of the file into a setup and a punchline."""
        line = line.strip()

        if line.startswith("- "):
            line = line[2:]

        if "?" not in line:
            return None

        # Split on the FIRST "?" only, so a "?" inside the punchline is kept
        setup, punchline = line.split("?", 1)
        setup = setup.strip() + "?"
        punchline = punchline.strip()

        if not punchline:
            return None

        return setup, punchline

    def loadJokes(self):
        """Read the jokes file once and return every valid joke."""
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
        """Build the header, the main area, the button bar and the side panel."""
        self.createHeader()

        body = tk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=25, pady=(8, 0))

        main = tk.Frame(body)
        main.pack(side="left", anchor="n")
        side = tk.Frame(body)
        side.pack(side="right", anchor="n", pady=(30, 0))

        self.createStage(main)
        self.createDock(self.stage)
        self.createFavouritesPanel(side)

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

    def createHeader(self):
        """Build the top row: the logo on the left and Quit on the right."""
        header = tk.Frame(self.root)
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

        sound_button = RoundedButton(
            header,
            soundLabel(),
            lambda: self.toggleSound(sound_button),
            width=130,
            height=38,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
        )
        sound_button.pack(side="right", padx=(0, 10))

    def toggleSound(self, button):
        """Switch the sound effects on or off and update the button text."""
        global sound_on
        sound_on = not sound_on
        if not sound_on:
            stopSound()
        button.itemconfig(button.label, text=soundLabel())

    def createStage(self, parent):
        """Build the main drawing area: waves, ring, joke bubble and drum."""
        stage = tk.Canvas(
            parent,
            width=STAGE_WIDTH,
            height=STAGE_HEIGHT,
            bg=BG,
            highlightthickness=0,
        )
        stage.pack()
        self.stage = stage

        stage.create_polygon(self.wavePoints(150, 26, 0.0), fill=WAVE_1, outline="")
        stage.create_polygon(self.wavePoints(250, 20, 2.0), fill=WAVE_2, outline="")

        self.drawRing()

        self.status_text = stage.create_text(
            RING_X, 226, text="", fill=MUTED, font=(FONT, 14, "italic")
        )
        self.dot_items = []
        for number in range(4):
            x = RING_X - 33 + number * 22
            self.dot_items.append(
                stage.create_oval(x - 5, 258, x + 5, 268, fill="#1E3350", outline="")
            )

        self.drawBubble()
        self.drawDrum()

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
            BUBBLE[2],
            BUBBLE[3] + 20,
            anchor="e",
            text="Jokes told: 0",
            fill=MUTED,
            font=(FONT, 10),
        )

    def wavePoints(self, base, height, shift):
        """Work out the points of one wave: a smooth curve with a flat bottom."""
        points = []
        for x in range(0, STAGE_WIDTH + 1, 10):
            points += [x, base + height * math.sin(x / 130 + shift)]

        points += [STAGE_WIDTH, STAGE_HEIGHT, 0, STAGE_HEIGHT]
        return points

    def drawRing(self):
        """Draw the glowing mic ring with a sound wave on each side."""
        stage = self.stage
        x, y = RING_X, RING_Y

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

        self.arc_items = []
        for radius in ARC_RADII:
            box = (x - radius, y - radius, x + radius, y + radius)
            left = stage.create_arc(*box, start=150, extent=60, style="arc", width=5)
            right = stage.create_arc(*box, start=-30, extent=60, style="arc", width=5)
            self.arc_items.append((left, right))

        self.ring = stage.create_oval(
            x - RING_RADIUS,
            y - RING_RADIUS,
            x + RING_RADIUS,
            y + RING_RADIUS,
            fill="#09101F",
            width=10,
        )

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
        """Draw the joke bubble and the text inside it (hidden until a joke starts)."""
        stage = self.stage
        left, top, right, bottom = BUBBLE

        roundedRectangle(stage, left, top, right, bottom, 30, BUBBLE_EDGE, "bubble")
        roundedRectangle(
            stage, left + 2, top + 2, right - 2, bottom - 2, 28, BUBBLE_FILL, "bubble"
        )

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
        """Draw a small drum and its text (hidden until the drum roll)."""
        stage = self.stage
        x, y = RING_X, 446

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

    def createDock(self, stage):
        """Build the rounded bar of buttons at the bottom of the main area."""
        # background=WAVE_2 is the colour of the wave behind the bar
        dock = Card(
            stage, width=740, height=84, radius=42, fill=DOCK, background=WAVE_2
        )
        stage.create_window(STAGE_WIDTH // 2, STAGE_HEIGHT - 68, window=dock)
        body = dock.body

        quiet = dict(
            height=52,
            fill=CARD,
            hover=CARD_HOVER,
            text_colour=TEXT,
            background=DOCK,
        )

        self.save_button = RoundedButton(
            body, "♥  Save", self.addFavourite, width=110, **quiet
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
            """Show the hint only while the search box is empty."""
            if self.search_entry.get():
                hint.place_forget()
            else:
                hint.place(x=2, y=0, relheight=1)

        self.search_entry.bind("<KeyRelease>", updateHint)
        updateHint()

    def createFavouritesPanel(self, parent):
        """Build the side panel that lists the saved jokes."""
        card = Card(parent, width=270, height=430, radius=26, fill=PANEL)
        card.pack()
        body = card.body

        title = tk.Frame(body, bg=PANEL)
        title.pack(fill="x", padx=8, pady=(6, 0))
        tk.Label(title, text="★", font=(FONT, 16), fg=STAR, bg=PANEL).pack(side="left")
        tk.Label(title, text="Your Favourites", font=(FONT, 14, "bold"), bg=PANEL).pack(
            side="left", padx=8
        )

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

    def pickJoke(self):
        """Deal the next joke from a shuffled queue."""
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
        """Handle the joke buttons: tell the next random joke."""
        if not self.jokes:
            return  # nothing to tell (also protects the Enter shortcut)

        self.startJoke(self.pickJoke())

    def startJoke(self, joke):
        """Start telling a joke: the ring pulses, then the setup is typed out."""
        self.cancelAnimations()
        playSound("chime.wav")

        self.current_joke = joke
        self.jokes_told += 1
        self.after_message = ("", MUTED)

        self.stage.itemconfig("bubble", state="normal")
        self.stage.itemconfig(self.setup_text, text="")
        self.stage.itemconfig(self.punchline_text, text="")
        self.stage.itemconfig("drum", state="hidden")
        self.stage.itemconfig(self.punch_window, state="hidden")
        self.stage.itemconfig(self.counter_text, text=f"Jokes told: {self.jokes_told}")

        self.save_button.setEnabled(False)
        self.next_button.setEnabled(True)

        self.setStatus("Thinking...")
        self.pulseRing(0, self.showSetup)

    def showSetup(self):
        """Type out the setup of the current joke."""
        setup, _ = self.current_joke
        self.setStatus(*self.after_message)
        self.typeText(self.setup_text, setup, when_done=self.enablePunchline)

    def enablePunchline(self):
        """Allow the punchline and saving once the setup has finished typing."""
        self.stage.itemconfig(self.punch_window, state="normal")
        self.save_button.setEnabled(True)

    def showPunchline(self):
        """Handle the Show Punchline button: drum roll, then type the punchline."""
        if self.current_joke is None:
            return

        self.stage.itemconfig(self.punch_window, state="hidden")
        self.stage.itemconfig("drum", state="normal")
        playSound("drumroll.wav")
        self.drumRoll(0)

    def setStatus(self, text, colour=MUTED):
        """Show a short message under the ring."""
        self.stage.itemconfig(self.status_text, text=text, fill=colour)

    def onSearchEnter(self, event):
        """Search when Enter is pressed in the search box."""
        self.searchJoke()
        return "break"  # stops Enter from also telling a random joke

    def searchJoke(self):
        """Tell a random joke that contains the word in the search box."""
        word = self.search_entry.get().strip()
        if not word:
            self.setStatus("Type a word to search for.")
            return

        matches = findJokes(self.jokes, word)
        if not matches:
            self.setStatus(f'No jokes about "{word}".', ERROR)
            return

        choices = [joke for joke in matches if joke != self.current_joke] or matches
        self.startJoke(random.choice(choices))

        # startJoke clears the message, so set it again for when the setup appears
        noun = "joke" if len(matches) == 1 else "jokes"
        self.after_message = (f'Found {len(matches)} {noun} about "{word}".', MUTED)

    def addFavourite(self):
        """Handle the Save button: add the joke on screen to the favourites."""
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
        """Save the favourites to the file, and warn if that fails."""
        if not saveFavourites(self.favourites):
            messagebox.showerror(
                "Save failed", "Your favourites could not be saved to the file."
            )

    def refreshFavourites(self):
        """Redraw the rows in the favourites panel."""
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

        self.fav_rows.update_idletasks()
        self.fav_canvas.config(scrollregion=self.fav_canvas.bbox("all"))
        self.fav_canvas.yview_moveto(0)

    def makeFavouriteRow(self, position, setup):
        """Add one rounded row: the joke's setup and a small delete cross."""
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
            text="✕",
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
        """Make the mouse wheel scroll the favourites list over this widget."""
        widget.bind("<MouseWheel>", self.scrollFavourites)

    def scrollFavourites(self, event):
        """Scroll the favourites list up or down by one step."""
        self.fav_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def tellFavourite(self, position):
        """Tell a saved joke again when its row is clicked."""
        if position < len(self.favourites):
            self.startJoke(self.favourites[position])

    def deleteFavourite(self, position):
        """Delete one joke from the favourites."""
        if position < len(self.favourites):
            del self.favourites[position]
            self.storeFavourites()
            self.refreshFavourites()

    def clearFavourites(self):
        """Delete every favourite, after asking for confirmation."""
        if not self.favourites:
            return

        if messagebox.askyesno("Clear all", "Delete all of your favourite jokes?"):
            self.favourites = []
            self.storeFavourites()
            self.refreshFavourites()

    def typeText(self, item, text, index=0, when_done=None):
        """Type text into a canvas text item one letter at a time."""
        cursor = "|" if index < len(text) else ""
        self.stage.itemconfig(item, text=text[:index] + cursor)

        if index < len(text):
            self.anim_job = self.root.after(
                TYPE_DELAY_MS,
                lambda: self.typeText(item, text, index + 1, when_done),
            )
        else:
            self.anim_job = None
            if when_done is not None:
                when_done()

    def drumRoll(self, step):
        """Show the drum for a moment, then type out the punchline."""
        if step < DRUM_ROLL_STEPS:
            dots = "." * (step % 3 + 1)
            self.stage.itemconfig(self.drum_text, text=f"* Drum roll{dots} *")
            self.moveSticks(step % 2 == 0)
            self.anim_job = self.root.after(
                DRUM_ROLL_DELAY_MS, lambda: self.drumRoll(step + 1)
            )
        else:
            self.stage.itemconfig("drum", state="hidden")

            _, punchline = self.current_joke
            bottom = self.stage.bbox(self.setup_text)[3]
            self.stage.coords(self.punchline_text, BUBBLE[0] + 32, bottom + 8)
            playSound("rimshot.wav")
            self.typeText(self.punchline_text, punchline)

    def moveSticks(self, left_up):
        """Move the drumsticks: one raised and one lowered, then the other way round."""
        x, y = RING_X, 446
        high_left = (x - 34, y - 46, x - 10, y - 20)
        low_left = (x - 34, y - 34, x - 10, y - 16)
        high_right = (x + 34, y - 46, x + 10, y - 20)
        low_right = (x + 34, y - 34, x + 10, y - 16)

        self.stage.coords(self.stick_left, *(high_left if left_up else low_left))
        self.stage.coords(self.stick_right, *(low_right if left_up else high_right))

    def setRing(self, mode):
        """Change how the ring looks."""
        colour, glow, wave_colours = RING_STYLES[mode]
        self.stage.itemconfig(self.ring, outline=colour, width=10)

        for item in self.glow_items:
            self.stage.itemconfig(item, state="normal" if glow else "hidden")

        for (left, right), wave_colour in zip(self.arc_items, wave_colours):
            self.stage.itemconfig(left, outline=wave_colour)
            self.stage.itemconfig(right, outline=wave_colour)

    def setDots(self, count):
        """Light up the first few of the four dots under the ring."""
        for number, dot in enumerate(self.dot_items):
            self.stage.itemconfig(dot, fill=ACCENT if number < count else "#1E3350")

    def pulseRing(self, step, when_done):
        """Make the ring pulse for a moment, then call a function."""
        if step < THINKING_STEPS:
            self.setRing("ready")
            width = RING_WIDTHS[step % len(RING_WIDTHS)]
            self.stage.itemconfig(self.ring, width=width)
            self.setDots(step % 5)
            self.anim_job = self.root.after(
                PULSE_DELAY_MS, lambda: self.pulseRing(step + 1, when_done)
            )
        else:
            self.anim_job = None
            self.setRing("ready")
            self.setDots(0)
            when_done()

    def cancelAnimations(self):
        """Stop the typing, drum roll or pulse if one is running."""
        stopSound()
        if self.anim_job is not None:
            self.root.after_cancel(self.anim_job)
            self.anim_job = None

    def quitApp(self):
        """Handle the Quit button: close the application."""
        self.cancelAnimations()
        self.root.destroy()


def main():
    """Create the Tkinter root window and start the event loop."""
    root = tk.Tk()
    JokeAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()
