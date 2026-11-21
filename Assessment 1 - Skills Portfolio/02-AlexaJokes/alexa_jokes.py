import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

#Constants
WINDOW_TITLE = "Alexa Tell Me a Joke"
WINDOW_SIZE = "550x350"
JOKES_FILE = Path(__file__).parent / "randomJokes.txt"
#Width in pixels at which long jokes wrap onto a new line
WRAP_LENGTH = 500

class JokeAssistant:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        #Joke state
        self.jokes = self.loadJokes() #List of (setup, punchline) tuples
        self.current_joke = None #The (setup, punchline) tuple on screen

        self.createWidgets()

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

        self.joke_button = tk.Button(self.root, text="Alexa tell me a Joke", font=("Arial", 12), width=22, command=self.tellJoke,)
        self.joke_button.pack(pady=5)

        #Setup label: wraplength makes long jokes wrap instead of running off screen
        self.setup_label = tk.Label(self.root, text="", font=("Arial", 14), wraplength=WRAP_LENGTH)
        self.setup_label.pack(pady=(25, 10))

        self.punchline_button = tk.Button(self.root, text="Show Punchline", font=("Arial", 12), width=22, state="disabled", command=self.showPunchline,)
        self.punchline_button.pack(pady=5)

        # Punchline label
        self.punchline_label = tk.Label(self.root, text="", font=("Arial", 14, "italic"), fg="blue", wraplength=WRAP_LENGTH,)
        self.punchline_label.pack(pady=10)

        #Without any jokes the button can't do anything, so switch it off
        if not self.jokes:
            self.joke_button.config(state="disabled")
            self.setup_label.config(text="No jokes available.", fg="red")

    def pickJoke(self, previous_joke):
        joke = random.choice(self.jokes)

        #Re-pick if we got the same joke again (only possible with 2+ jokes)
        while len(self.jokes) > 1 and joke == previous_joke:
            joke = random.choice(self.jokes)
        return joke

    def tellJoke(self):
        self.current_joke = self.pickJoke(self.current_joke)
        setup, _ = self.current_joke #The punchline stays hidden for now

        self.setup_label.config(text=setup, fg="black")
        self.punchline_label.config(text="") #Clear the previous punchline
        self.punchline_button.config(state="normal")

    def showPunchline(self):
        if self.current_joke is None:
            return   #No joke on screen, so nothing to reveal

        _, punchline = self.current_joke   #The setup is already showing
        self.punchline_label.config(text=punchline)
        self.punchline_button.config(state="disabled")   #Already revealed    

def main():
    root = tk.Tk()
    JokeAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()