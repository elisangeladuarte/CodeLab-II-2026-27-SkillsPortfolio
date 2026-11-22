import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

#Constants
WINDOW_TITLE = "Alexa Tell Me a Joke"
WINDOW_SIZE = "700x560"
#Width in pixels at which long jokes wrap onto a new line
WRAP_LENGTH = 600
JOKES_FILE = Path(__file__).parent / "randomJokes.txt"

#Colors 
BG = "#0B1220" #Window background
CARD = "#141C2F" #Greyed-out button background
ACCENT = "#2BB6F6" #Buttons and punchline
ACCENT_HOVER = "#5CC8F8"
TEXT = "#E8EEF9"
MUTED = "#8A96B0"
ERROR = "#FF6B7A"

#Animation timings (in milliseconds)
TYPE_DELAY_MS = 35 #Pause between typed letters
DRUM_ROLL_STEPS = 5 #How many times the drum roll dots change
DRUM_ROLL_DELAY_MS = 300 #Pause between drum roll steps

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

        self.next_button = ttk.Button(button_frame, text="Next Joke", width=12, state="disabled", command=self.tellJoke,)
        self.next_button.pack(side="left", padx=10)

        ttk.Button(button_frame, text="Quit", width=12, command=self.quitApp,).pack(side="left", padx=10)    

        self.counter_label = tk.Label(
            self.root, text="Jokes told: 0", font=("Arial", 10), fg=MUTED
        )
        self.counter_label.pack(pady=(5, 0))            

        #Without any jokes the button can't do anything, so switch it off
        if not self.jokes:
            self.joke_button.config(state="disabled")
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

        self.cancelAnimations() #Stop any typing or drum roll still running

        self.current_joke = self.pickJoke()
        self.jokes_told += 1
        setup, _ = self.current_joke #The punchline stays hidden for now

        self.setup_label.config(fg=TEXT)
        self.punchline_label.config(text="") #Clear the previous punchline
        self.punchline_button.config(state="disabled") #Until the setup is typed
        self.next_button.config(state="normal")
        self.counter_label.config(text=f"Jokes told: {self.jokes_told}")

        self.typeText(self.setup_label, setup, when_done=self.enablePunchline)

    def enablePunchline(self):
        self.punchline_button.config(state="normal")

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