import json
import math
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

#Constants
WINDOW_TITLE = "Alexa Tell Me a Joke"
WINDOW_SIZE = "1100x680"

# Size (in pixels) of the main drawing area (ring, joke and button bar)
STAGE_WIDTH = 780
STAGE_HEIGHT = 610

# Colours (kept in one place so the whole look can be changed easily)
BG = "#0A1020"        # Window background
PANEL = "#101830"     # The favourites panel
DOCK = "#0F1730"      # The bar of buttons at the bottom
CARD = "#141E3A"      # Dark pill buttons and rows
CARD_HOVER = "#1C2850"
ACCENT = "#2BB6F6"    # Main button and the punchline
ACCENT_HOVER = "#5CC8F8"
BRIGHT = "#38D0FF"    # The glowing ring
DARK = "#06101F"      # Dark text on the bright button
TEXT = "#E8EEF9"
MUTED = "#8A96B0"
OFF = "#55607A"       # text on a disabled button
ERROR = "#FF6B7A"
SUCCESS = "#3DDC97"
STAR = "#F5B83D"
BUBBLE_EDGE = "#4F6FE8"   # outline of the joke bubble
BUBBLE_FILL = "#0F1730"
WAVE_1 = "#0C1530"        # the two soft waves in the background
WAVE_2 = "#0B1228"

# Fonts
FONT = "Segoe UI"         # falls back to a default font if it isn't installed
MONO = "Consolas"         # the joke text looks like it is being typed

# Animation timings (in milliseconds)
TYPE_DELAY_MS = 35        # Pause between typed letters
DRUM_ROLL_STEPS = 6       # How many times the drum roll changes
DRUM_ROLL_DELAY_MS = 300  # Pause between drum roll steps
PULSE_DELAY_MS = 120      # Pause between steps of the ring pulse
THINKING_STEPS = 10       # How many pulse steps before the joke appears

# The mic ring (drawn on the stage canvas)
RING_X = STAGE_WIDTH // 2     # Centre of the ring
RING_Y = 112
RING_RADIUS = 80
RING_WIDTHS = [8, 11, 14, 11]   # Ring thickness at each step of the pulse
GLOW_CIRCLES = [(104, "#0E1F3A"), (98, "#10294A"), (92, "#133559")]   # (radius, colour)
ARC_RADII = [96, 112, 128]      # The sound waves on each side of the ring

# Ring styles: mode -> (ring colour, glow visible?, colours of the three sound waves)
RING_STYLES = {
    "idle": ("#1F3A5A", False, ["#16304A", "#122740", "#0F2036"]),
    "ready": (BRIGHT, True, ["#2AA8E6", "#1C6E9E", "#134666"]),
}

# The joke bubble: left, top, right, bottom
BUBBLE = (70, 276, 710, 416)
BUBBLE_TEXT_WIDTH = 576   # Long jokes wrap at this width

def loadFavourites():
    try:
        with open(FAVOURITES_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    favourites = []
    if isinstance(saved, list):
        for item in saved:
            #Each joke was saved as [setup, punchline]
            if isinstance(item, list) and len(item) == 2:
                favourites.append((str(item[0]), str(item[1])))
    return favourites

def saveFavourites(favourites):
    try:
        with open(FAVOURITES_FILE, "w", encoding="utf-8") as file:
            json.dump(favourites, file, indent=2) #Tuples are saved as lists
    except OSError:
        return False
    return True

def findJokes(jokes, word):
    word = word.lower()
    return [
        joke for joke in jokes
        if word in joke[0].lower() or word in joke[1].lower()
    ]

class JokeAssistant:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self.setupStyle()

        #Joke state
        self.jokes = self.loadJokes() #List of (setup, punchline) tuples
        self.current_joke = None #The (setup, punchline) tuple on screen
        self.joke_queue = [] #Shuffled jokes still to be told
        self.jokes_told = 0 #Counter shown to the user
        self.anim_job = None #The pending root.after call, so we cancel it
        self.favourites = loadFavourites() #Saved (setup, punchline) tuples
        self.fav_window = None #The favourites window, when it is open
        self.fav_list = None
        self.fav_detail = None        

        self.createWidgets()

        #Keyboard shortcuts
        self.root.bind("<Return>", lambda event: self.tellJoke())
        self.root.bind("<Escape>", lambda event: self.quitApp())

    def setupStyle(self):
        self.root.configure(bg=BG)

        #Default colours for every Label and Frame created from now on
        self.root.option_add("*Label.background", BG)
        self.root.option_add("*Label.foreground", TEXT)
        self.root.option_add("*Frame.background", BG)

        #"clam" is a ttk theme that lets us colour buttons on every system
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
            "TScrollbar", background=ACCENT, troughcolor=CARD, arrowcolor=BG,
            bordercolor=CARD, lightcolor=ACCENT, darkcolor=ACCENT,
        )
        style.map("TScrollbar", background=[("active", ACCENT_HOVER)])    

    def parseJoke(self, line):
        line = line.strip()

        #Remove a leading "- " list marker if the file has one
        if line.startswith("- "):
            line = line[2:]

        #Skip blank lines and lines with no question mark
        if "?" not in line:
            return None

        #Split on the FIRST "?" only, so a "?" inside the punchline is kept
        setup, punchline = line.split("?", 1)
        setup = setup.strip() + "?"  #Put the question mark back
        punchline = punchline.strip()

        #A line ending in "?" with nothing after it has no punchline
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
            messagebox.showerror("File not found", f"Could not find the jokes file:\n{JOKES_FILE}",)
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("Error reading jokes", f"The jokes file could not be read:\n{error}")
        return jokes

    def createWidgets(self):
        tk.Label(self.root, text="Joke Assistant", font=("Arial", 22, "bold")).pack(pady=(25, 15))

        self.joke_button = ttk.Button(self.root, text="Alexa tell me a Joke", width=22, command=self.tellJoke,)
        self.joke_button.pack(pady=5)

        #Search row: type a word, then press Enter or click Go
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=(10, 0))

        tk.Label(search_frame, text="Joke about:", font=("Arial", 11)).pack(
            side="left", padx=(0, 8)
        )
        self.search_entry = tk.Entry(
            search_frame, font=("Arial", 12), width=20, bg=CARD, fg=TEXT,
            insertbackground=TEXT, relief="flat", highlightthickness=1,
            highlightbackground=CARD, highlightcolor=ACCENT,
            disabledbackground=CARD,
        )
        self.search_entry.pack(side="left", ipady=4)
        self.search_entry.bind("<Return>", self.onSearchEnter)

        self.search_button = ttk.Button(
            search_frame, text="Go", width=6, command=self.searchJoke
        )
        self.search_button.pack(side="left", padx=(8, 0))

        tk.Label(self.root, text="Joke Assistant", font=("Arial", 22, "bold")).pack(pady=(20, 5))

        #The Echo ring: a glow circle behind a thicker ring, with a small label
        self.ring_canvas = tk.Canvas(self.root, width=RING_SIZE, height=RING_SIZE, bg=BG, highlightthickness=0,)
        self.ring_canvas.pack(pady=(0, 10))
        self.ring_glow = self.ring_canvas.create_oval(5, 5, RING_SIZE - 5, RING_SIZE - 5, outline=BG, width=2)
        self.ring = self.ring_canvas.create_oval(20, 20, RING_SIZE - 20, RING_SIZE - 20, outline=BG, width=6)
        self.ring_canvas.create_text(RING_SIZE / 2, RING_SIZE / 2, text="alexa", fill=MUTED, font=("Arial", 11),)
        self.setRing("idle")

        #Setup label: wraplength makes long jokes wrap instead of running off screen
        self.setup_label = tk.Label(self.root, text="", font=("Arial", 14), wraplength=WRAP_LENGTH, height=2,)
        self.setup_label.pack(pady=(25, 10))

        self.punchline_button = ttk.Button(self.root, text="Show Punchline", width=22, state="disabled", command=self.showPunchline,)
        self.punchline_button.pack(pady=5)

        #Punchline label
        self.punchline_label = tk.Label(self.root, text="", font=("Arial", 14, "italic"), fg=ACCENT, wraplength=WRAP_LENGTH, height=2,)
        self.punchline_label.pack(pady=10)

        #Next Joke and Quit sit side by side inside a frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(20, 10))

        self.next_button = ttk.Button(button_frame, text="Next Joke", width=12,  state="disabled", command=self.tellJoke,)
        self.next_button.pack(side="left", padx=8)

        self.save_button = ttk.Button( button_frame, text="Save Joke", width=12, state="disabled", command=self.addFavourite,)
        self.save_button.pack(side="left", padx=8)

        ttk.Button(button_frame, text="Favourites", width=12, command=self.openFavourites,).pack(side="left", padx=8)

        ttk.Button(button_frame, text="Quit", width=12, command=self.quitApp,).pack(side="left", padx=8)

        self.counter_label = tk.Label(
            self.root, text="Jokes told: 0", font=("Arial", 10), fg=MUTED
        )
        self.counter_label.pack(pady=(5, 0))  

        #Short messages such as "Saved to your favourites."
        self.status_label = tk.Label(self.root, text="", font=("Arial", 10))
        self.status_label.pack(pady=(2, 0))          

        #Without any jokes the button can't do anything, so switch it off
        if not self.jokes:
            self.joke_button.config(state="disabled")
            self.search_entry.config(state="disabled")
            self.search_button.config(state="disabled")
            self.setup_label.config(text="No jokes available.", fg=ERROR)

    def pickJoke(self, previous_joke=None):
        if not self.joke_queue:
            self.joke_queue = self.jokes.copy()
            random.shuffle(self.joke_queue)

            #Avoid telling the same joke twice in a row across two rounds
            if len(self.joke_queue) > 1 and self.joke_queue[-1] == self.current_joke:
                self.joke_queue[0], self.joke_queue[-1] = (
                    self.joke_queue[-1], self.joke_queue[0],
                )

        return self.joke_queue.pop()

    def tellJoke(self):
        if not self.jokes:
            return #Nothing to tell (also protects the Enter shortcut)

        self.startJoke(self.pickJoke())

    def startJoke(self, joke):
        self.cancelAnimations() #Stop any typing or drum roll still running

        self.current_joke = joke
        self.jokes_told += 1

        self.setup_label.config(text="Thinking...", fg=MUTED)
        self.punchline_label.config(text="") #Clear the previous punchline
        self.punchline_button.config(state="disabled") #Until the setup is typed
        self.save_button.config(state="disabled")
        self.status_label.config(text="")
        self.next_button.config(state="normal")
        self.counter_label.config(text=f"Jokes told: {self.jokes_told}")

        #The ring pulses while Alexa "thinks", then the setup is typed out
        self.pulseRing(0, self.showSetup)

    def showSetup(self):
        setup, _ = self.current_joke
        self.setup_label.config(fg=TEXT)
        self.typeText(self.setup_label, setup, when_done=self.enablePunchline)

    def enablePunchline(self):
        self.punchline_button.config(state="normal")
        self.save_button.config(state="normal")

    def showPunchline(self):
        if self.current_joke is None:
            return #No joke on screen, so nothing to reveal

        self.punchline_button.config(state="disabled") #Already revealing
        self.drumRoll(0) 

    def typeText(self, label, text, index=0, when_done=None):
        label.config(text=text[:index])

        if index < len(text):
            #Call this same method again shortly, with one more letter
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
            dots = "." * (step % 3 + 1) #Cycles through 1, 2 and 3 dots
            self.punchline_label.config(text=f"Drum roll{dots}", fg=MUTED)
            self.anim_job = self.root.after(
                DRUM_ROLL_DELAY_MS, lambda: self.drumRoll(step + 1)
            )
        else:
            _, punchline = self.current_joke
            self.punchline_label.config(fg=ACCENT)
            self.typeText(self.punchline_label, punchline)

    def setRing(self, mode):
        width, colour, glow = RING_STYLES[mode]
        self.ring_canvas.itemconfig(self.ring, width=width, outline=colour)
        self.ring_canvas.itemconfig(self.ring_glow, outline=glow)

    def pulseRing(self, step, when_done):
        if step < THINKING_STEPS:
            width = RING_WIDTHS[step % len(RING_WIDTHS)]   # cycles through the list
            self.ring_canvas.itemconfig(self.ring, width=width, outline=ACCENT)
            self.ring_canvas.itemconfig(self.ring_glow, outline=BG)
            self.anim_job = self.root.after(
                PULSE_DELAY_MS, lambda: self.pulseRing(step + 1, when_done)
            )
        else:
            self.anim_job = None
            self.setRing("ready")
            when_done()

    #Search
    def onSearchEnter(self, event):
        self.searchJoke()
        return "break" #Stops Enter from also telling a random joke

    def searchJoke(self):
        word = self.search_entry.get().strip()
        if not word:
            self.status_label.config(text="Type a word to search for.", fg=MUTED)
            return

        matches = findJokes(self.jokes, word)
        if not matches:
            self.status_label.config(text=f"No jokes about \"{word}\".", fg=ERROR)
            return

        #Avoid telling the joke that is already on screen, if there is a choice
        choices = [joke for joke in matches if joke != self.current_joke] or matches
        self.startJoke(random.choice(choices))

        #startJoke clears the status label, so show the count afterwards
        noun = "joke" if len(matches) == 1 else "jokes"
        self.status_label.config(
            text=f"Found {len(matches)} {noun} about \"{word}\".", fg=MUTED
        )            

    #Favourites
    def addFavourite(self):
        if self.current_joke is None:
            return

        if self.current_joke in self.favourites:
            self.status_label.config(text="Already in your favourites.", fg=MUTED)
            return

        self.favourites.append(self.current_joke)
        self.storeFavourites()
        self.status_label.config(text="Saved to your favourites.", fg=SUCCESS)
        self.refreshFavourites() #Update the favourites window if it is open

    def storeFavourites(self):
        if not saveFavourites(self.favourites):
            messagebox.showerror(
                "Save failed", "Your favourites could not be saved to the file."
            )

    def openFavourites(self):
        if self.fav_window is not None and self.fav_window.winfo_exists():
            self.fav_window.lift()
            return

        window = tk.Toplevel(self.root)
        window.title("Favourite jokes")
        window.geometry("560x430")
        window.configure(bg=BG)
        window.transient(self.root)
        window.bind("<Escape>", lambda event: window.destroy())
        self.fav_window = window

        tk.Label(
            window, text="Your Favourites", font=("Arial", 18, "bold")
        ).pack(pady=(15, 10))

        #The list of setups, with a scrollbar
        list_frame = tk.Frame(window)
        list_frame.pack(fill="both", expand=True, padx=20)

        self.fav_list = tk.Listbox(
            list_frame, font=("Arial", 12), bg=CARD, fg=TEXT,
            selectbackground=ACCENT, selectforeground=BG,
            highlightthickness=0, relief="flat", activestyle="none",
        )
        scrollbar = ttk.Scrollbar(list_frame, command=self.fav_list.yview)
        self.fav_list.config(yscrollcommand=scrollbar.set)
        self.fav_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.fav_list.bind("<<ListboxSelect>>", self.showFavouritePunchline)

        #Shows the punchline of the selected joke
        self.fav_detail = tk.Label(
            window, text="", font=("Arial", 12, "italic"), fg=ACCENT,
            wraplength=500, height=2,
        )
        self.fav_detail.pack(pady=10)

        buttons = tk.Frame(window)
        buttons.pack(pady=(0, 15))
        ttk.Button(
            buttons, text="Delete selected", width=14, command=self.deleteFavourite
        ).pack(side="left", padx=6)
        ttk.Button(
            buttons, text="Clear all", width=10, command=self.clearFavourites
        ).pack(side="left", padx=6)
        ttk.Button(
            buttons, text="Close", width=10, command=window.destroy
        ).pack(side="left", padx=6)

        self.refreshFavourites()

    def refreshFavourites(self):
        if self.fav_window is None or not self.fav_window.winfo_exists():
            return

        self.fav_list.delete(0, tk.END)
        for setup, _ in self.favourites:
            self.fav_list.insert(tk.END, setup)

        if self.favourites:
            self.fav_detail.config(text="Select a joke to see its punchline.", fg=MUTED)
        else:
            self.fav_detail.config(text="No favourites yet.", fg=MUTED)

    def showFavouritePunchline(self, event=None):
        selection = self.fav_list.curselection() #A tuple of selected positions
        if selection:
            _, punchline = self.favourites[selection[0]]
            self.fav_detail.config(text=punchline, fg=ACCENT)

    def deleteFavourite(self):
        selection = self.fav_list.curselection()
        if not selection:
            self.fav_detail.config(text="Select a joke to delete first.", fg=MUTED)
            return

        del self.favourites[selection[0]]
        self.storeFavourites()
        self.refreshFavourites()

    def clearFavourites(self):
        if not self.favourites:
            return

        if messagebox.askyesno(
            "Clear all", "Delete all of your favourite jokes?", parent=self.fav_window
        ):
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
    root.mainloop()

if __name__ == "__main__":
    main()