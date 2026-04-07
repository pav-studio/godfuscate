import os
import json
import random
import string
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext

# -----------------------------
# Load security config
# -----------------------------

with open("security.json") as f:
    config = json.load(f)

WORDS = []
if os.path.exists("word_pool.txt"):
    WORDS = open("word_pool.txt").read().splitlines()

CONFUSING = ["I", "l", "1", "O", "0"]

def generate_name():

    length = random.randint(
        config["min_length"],
        config["max_length"]
    )

    pool = ""

    if config["use_lowercase"]:
        pool += string.ascii_lowercase

    if config["use_uppercase"]:
        pool += string.ascii_uppercase

    if config["use_numbers"]:
        pool += string.digits

    if config.get("confusing_names", False):
        pool += "".join(CONFUSING)

    rand = ''.join(random.choice(pool) for _ in range(length))

    if WORDS:
        word = random.choice(WORDS)
        rand = word + rand

    return config["prefix"] + rand + config["suffix"]


# -----------------------------
# GUI
# -----------------------------

PLATFORMS = [
    "Windows Desktop",
    "Linux/X11",
    "Web",
    "Android"
]

class BuilderUI:

    def __init__(self, root):
        self.root = root
        root.title("Godot Secure Builder")
        root.geometry("900x650")
        root.configure(bg="#202124")

        self.setup_theme()
        self.build_ui()

    def setup_theme(self):
        self.bg = "#202124"
        self.panel = "#2b2c2f"
        self.text = "#e8eaed"
        self.sub = "#9aa0a6"
        self.accent = "#8ab4f8"

    def build_ui(self):

        container = tk.Frame(self.root, bg=self.bg)
        container.pack(fill="both", expand=True, padx=14, pady=14)

        # PROJECT
        tk.Label(container, text="Godot Project",
                 fg=self.text, bg=self.bg).pack(anchor="w")

        row = tk.Frame(container, bg=self.bg)
        row.pack(fill="x", pady=(4,10))

        self.project_var = tk.StringVar()

        tk.Entry(
            row,
            textvariable=self.project_var,
            bg=self.panel,
            fg=self.text,
            insertbackground=self.text,
            relief="flat"
        ).pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(
            row,
            text="Browse",
            command=self.browse_project,
            bg=self.panel,
            fg=self.text,
            relief="flat"
        ).pack(side="left", padx=6)

        # GODOT
        tk.Label(container, text="Godot CLI",
                 fg=self.text, bg=self.bg).pack(anchor="w")

        row = tk.Frame(container, bg=self.bg)
        row.pack(fill="x", pady=(4,10))

        default_godot = os.path.join(
            os.path.dirname(__file__),
            "godot"
        )

        self.godot_var = tk.StringVar(value=default_godot)

        tk.Entry(
            row,
            textvariable=self.godot_var,
            bg=self.panel,
            fg=self.text,
            insertbackground=self.text,
            relief="flat"
        ).pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(
            row,
            text="Browse",
            command=self.browse_godot,
            bg=self.panel,
            fg=self.text,
            relief="flat"
        ).pack(side="left", padx=6)

        # PLATFORMS
        tk.Label(container, text="Platforms",
                 fg=self.text, bg=self.bg).pack(anchor="w")

        grid = tk.Frame(container, bg=self.bg)
        grid.pack(fill="x", pady=8)

        self.platform_vars = {}

        cols = 3

        for i, p in enumerate(PLATFORMS):
            var = tk.BooleanVar()
            self.platform_vars[p] = var

            cb = tk.Checkbutton(
                grid,
                text=p,
                variable=var,
                fg=self.text,
                bg=self.bg,
                selectcolor=self.panel,
                activebackground=self.bg
            )

            r = i // cols
            c = i % cols

            cb.grid(row=r, column=c, padx=12, pady=8, sticky="w")

        # BUILD BUTTON
        tk.Button(
            container,
            text="BUILD",
            command=self.build,
            bg=self.accent,
            fg="black",
            relief="flat",
            pady=8
        ).pack(fill="x", pady=12)

        # TERMINAL
        tk.Label(container, text="Terminal",
                 fg=self.sub, bg=self.bg).pack(anchor="w")

        self.terminal = scrolledtext.ScrolledText(
            container,
            bg="#111111",
            fg="#e8eaed",
            insertbackground="white",
            relief="flat",
            height=16
        )

        self.terminal.pack(fill="both", expand=True)

    def log(self, text):
        self.terminal.insert("end", text + "\n")
        self.terminal.see("end")
        self.root.update()

    def browse_project(self):
        path = filedialog.askdirectory()
        if path:
            self.project_var.set(path)

    def browse_godot(self):
        path = filedialog.askopenfilename()
        if path:
            self.godot_var.set(path)

    # -----------------------------
    # BUILD PIPELINE
    # -----------------------------

    def build(self):

        project = self.project_var.get()
        godot = self.godot_var.get()

        if not project:
            self.log("No project selected")
            return

        selected = [
            p for p,v in self.platform_vars.items()
            if v.get()
        ]

        if not selected:
            self.log("No platforms selected")
            return

        build_dir = os.path.join(project, "build")
        tmp_dir = os.path.join(build_dir, "tmp")

        self.log("Preparing build folders...")

        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(tmp_dir, exist_ok=True)

        for p in selected:
            name = p.split()[0].lower()
            os.makedirs(os.path.join(build_dir, name), exist_ok=True)

        # copy project
        self.log("Copying project...")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        shutil.copytree(project, tmp_dir, ignore=shutil.ignore_patterns("build"))

        # rename files
        self.log("Preparing secure build...")
               # export
        for p in selected:

            self.log(f"Building {p}")

            output = os.path.join(
                build_dir,
                p.split()[0].lower()
            )

            cmd = [
                godot,
                "--headless",
                "--export-release",
                p
            ]

            subprocess.run(cmd, cwd=tmp_dir)

            self.log(f"Done {p}")

        self.log("Build finished")


root = tk.Tk()
app = BuilderUI(root)
root.mainloop()