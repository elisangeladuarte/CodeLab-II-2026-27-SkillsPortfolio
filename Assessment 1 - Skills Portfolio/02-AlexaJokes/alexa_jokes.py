import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

#Constants
WINDOW_TITLE = "Alexa Tell Me a Joke"
WINDOW_SIZE = "550x350"
JOKES_FILE = Path(__file__).parent / "randomJokes.txt"

class JokeAssistant:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        #Joke state
        self.jokes = self.loadJokes() #List of (setup, punchline) tuples
        self.current_joke = None #The (setup, punchline) tuple on screen

        self.placeholder = tk.Label(self.root, text="Alexa, tell me a joke", font=("Arial", 20, "bold"))
        self.placeholder.pack(pady=120)

        print(f"Loaded {len(self.jokes)} jokes")
        if self.jokes:
            print("First joke:", self.jokes[0])
            print("Random joke:", random.choice(self.jokes))

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

def main():
    root = tk.Tk()
    JokeAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()