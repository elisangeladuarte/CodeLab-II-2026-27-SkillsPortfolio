import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

#Constants
WINDOW_TITLE = "Alexa Tell Me a Joke"
WINDOW_SIZE = "550x350"
#Build the path from this script's location so it works from any folder
JOKES_FILE = Path(__file__).parent / "randomJokes.txt"

class JokeAssistant:

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        # Joke state
        self.jokes = [] #List of (setup, punchline) tuples, loaded in step 2
        self.current_joke = None #The (setup, punchline) tuple on screen

        self.placeholder = tk.Label(
            self.root, text="Alexa, tell me a joke", font=("Arial", 20, "bold")
        )
        self.placeholder.pack(pady=120)


def main():
    root = tk.Tk()
    JokeAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()