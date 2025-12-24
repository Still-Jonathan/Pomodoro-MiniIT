import tkinter as tk
from tkinter import ttk
import json
import os


class Pomodoro:
    def __init__(self, root):
        self.root = root

        # ---------------- FILES ----------------
        self.sessionsFile = "sessions.json"
        self.statsFile = "stats.json"

        # ---------------- TIMER ----------------
        self.totalSeconds = 0
        self.phaseTotal = 1
        self.timerRunning = False
        self.currentJob = None

        # ---------------- UI STATE ----------------
        self.dark_mode = False
        self.row_palette_index = 0

        # ---------------- DATA ----------------
        self.sessions = self.load_sessions()

        # ---------------- UI VARS ----------------
        self.timeString = tk.StringVar(value="00:00")
        self.style = ttk.Style()

        # ---------------- UI REFS ----------------
        self.sessionTree = None
        self.pauseButton = None
        self.progress = None

    # ======================================================
    # DATA
    # ======================================================

    def load_sessions(self):
        if not os.path.exists(self.sessionsFile):
            data = [
                {"name": "Pomodoro (25/5)", "work": 25, "break": 5, "cycles": 4},
                {"name": "Short Sprint (15/3)", "work": 15, "break": 3, "cycles": 4},
                {"name": "Long Focus (50/10)", "work": 50, "break": 10, "cycles": 2},
            ]
            with open(self.sessionsFile, "w") as f:
                json.dump(data, f, indent=2)
            return data

        with open(self.sessionsFile, "r") as f:
            return json.load(f)

    def save_sessions(self):
        with open(self.sessionsFile, "w") as f:
            json.dump(self.sessions, f, indent=2)

    # ======================================================
    # TREEVIEW
    # ======================================================

    def refresh_tree(self):
        self.sessionTree.delete(*self.sessionTree.get_children())
        for i, s in enumerate(self.sessions):
            self.sessionTree.insert(
                "", "end", iid=str(i),
                values=(s["name"], s["work"], s["break"], s["cycles"]),
                tags=(f"row{i % 10}",)
            )
        self.apply_row_colours()

    def selected_index(self):
        sel = self.sessionTree.selection()
        return int(sel[0]) if sel else None

    def edit_cell(self, event):
        row = self.sessionTree.identify_row(event.y)
        col = self.sessionTree.identify_column(event.x)
        if not row or col == "#0":
            return

        x, y, w, h = self.sessionTree.bbox(row, col)
        value = self.sessionTree.set(row, col)

        entry = tk.Entry(self.sessionTree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, value)
        entry.focus()

        def save(e=None):
            self.sessionTree.set(row, col, entry.get())
            self.sync_tree_to_sessions()
            entry.destroy()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def sync_tree_to_sessions(self):
        self.sessions.clear()
        for iid in self.sessionTree.get_children():
            v = self.sessionTree.item(iid, "values")
            self.sessions.append({
                "name": v[0],
                "work": int(v[1]),
                "break": int(v[2]),
                "cycles": int(v[3])
            })

    # ======================================================
    # BUTTONS
    # ======================================================

    def add_session(self):
        self.sessions.append({"name": "New Session", "work": 25, "break": 5, "cycles": 1})
        self.refresh_tree()

    def remove_session(self):
        idx = self.selected_index()
        if idx is not None:
            del self.sessions[idx]
            self.refresh_tree()

    def move_up(self):
        idx = self.selected_index()
        if idx and idx > 0:
            self.sessions[idx - 1], self.sessions[idx] = self.sessions[idx], self.sessions[idx - 1]
            self.refresh_tree()
            self.sessionTree.selection_set(idx - 1)

    def move_down(self):
        idx = self.selected_index()
        if idx is not None and idx < len(self.sessions) - 1:
            self.sessions[idx + 1], self.sessions[idx] = self.sessions[idx], self.sessions[idx + 1]
            self.refresh_tree()
            self.sessionTree.selection_set(idx + 1)

    # ======================================================
    # TIMER (STABLE)
    # ======================================================

    def start_selected(self):
        idx = self.selected_index()
        if idx is None:
            return

        self.totalSeconds = self.sessions[idx]["work"] * 60
        self.phaseTotal = max(1, self.totalSeconds)
        self.timerRunning = True
        self.progress["value"] = 0
        self.run_timer()

    def run_timer(self):
        if not self.timerRunning:
            return

        if self.totalSeconds > 0:
            self.totalSeconds -= 1
            self.update_time()
            self.progress["value"] = (self.phaseTotal - self.totalSeconds) / self.phaseTotal * 100
            self.currentJob = self.root.after(1000, self.run_timer)
        else:
            self.timerRunning = False
            self.timeString.set("Finished")

    def pause_resume(self):
        self.timerRunning = not self.timerRunning
        self.pauseButton.config(text="Resume" if not self.timerRunning else "Pause")
        if self.timerRunning:
            self.run_timer()

    def stop_timer(self):
        self.timerRunning = False
        if self.currentJob:
            self.root.after_cancel(self.currentJob)
        self.timeString.set("00:00")
        self.progress["value"] = 0

    def update_time(self):
        m, s = divmod(self.totalSeconds, 60)
        self.timeString.set(f"{m:02d}:{s:02d}")

    # ======================================================
    # THEMES
    # ======================================================

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_ui_theme()
        self.apply_row_colours()

    def cycle_row_palette(self):
        self.row_palette_index = (self.row_palette_index + 1) % 10
        self.apply_row_colours()

    def apply_ui_theme(self):
        if self.dark_mode:
            bg, fg = "#1e1e1e", "#ffffff"
            tree_bg = "#252526"
        else:
            bg, fg = "#f0f0f0", "#000000"
            tree_bg = "#ffffff"

        self.root.configure(bg=bg)
        self.style.theme_use("clam")
        self.style.configure("Treeview",
                             background=tree_bg,
                             foreground=fg,
                             fieldbackground=tree_bg,
                             rowheight=26)

    def apply_row_colours(self):
        light_palettes = [
            ["#e8f4ff", "#fff0e6", "#e6ffe6", "#f9e6ff", "#ffe6e6",
             "#e6f9ff", "#f0ffe6", "#fffbe6", "#f2e6ff", "#e6fff7"]
        ]

        dark_palettes = [
            ["#264653", "#6a040f", "#2a9d8f", "#5a189a", "#7f5539",
             "#003049", "#386641", "#4a4e69", "#540b0e", "#1b4332"]
        ]

        palette = dark_palettes[0] if self.dark_mode else light_palettes[0]

        for i in range(10):
            self.sessionTree.tag_configure(f"row{i}", background=palette[(i + self.row_palette_index) % 10])

    # ======================================================
    # UI
    # ======================================================

    def main(self):
        left = tk.Frame(self.root)
        left.pack(side=tk.LEFT, padx=10, pady=10)

        right = tk.Frame(self.root)
        right.pack(side=tk.RIGHT, padx=10, pady=10, expand=True)

        tk.Label(left, text="Sessions", font=("Arial", 14, "bold")).pack()

        cols = ("name", "work", "break", "cycles")
        self.sessionTree = ttk.Treeview(left, columns=cols, show="headings", height=12)
        for c in cols:
            self.sessionTree.heading(c, text=c.capitalize())
            self.sessionTree.column(c, width=90, anchor="center")

        self.sessionTree.column("name", width=220, anchor="w")
        self.sessionTree.pack()
        self.sessionTree.bind("<Double-1>", self.edit_cell)

        btns = tk.Frame(left)
        btns.pack(pady=6)
        tk.Button(btns, text="Add", command=self.add_session).grid(row=0, column=0, padx=2)
        tk.Button(btns, text="Remove", command=self.remove_session).grid(row=0, column=1, padx=2)
        tk.Button(btns, text="Save", command=self.save_sessions).grid(row=0, column=2, padx=2)

        move = tk.Frame(left)
        move.pack()
        tk.Button(move, text="Up", command=self.move_up).grid(row=0, column=0, padx=2)
        tk.Button(move, text="Down", command=self.move_down).grid(row=0, column=1, padx=2)

        tk.Label(right, textvariable=self.timeString,
                 font=("Arial", 36, "bold")).pack(pady=20)

        self.progress = ttk.Progressbar(right, length=320)
        self.progress.pack(pady=10)

        ctrl = tk.Frame(right)
        ctrl.pack()
        tk.Button(ctrl, text="Start Selected", command=self.start_selected).grid(row=0, column=0, padx=5)
        self.pauseButton = tk.Button(ctrl, text="Pause", command=self.pause_resume)
        self.pauseButton.grid(row=0, column=1, padx=5)
        tk.Button(ctrl, text="Stop", command=self.stop_timer).grid(row=0, column=2, padx=5)

        tk.Button(right, text="No Blue Ray Light pls", command=self.toggle_dark_mode).pack(pady=4)
        tk.Button(right, text="Change Row Colours", command=self.cycle_row_palette).pack(pady=4)

        self.refresh_tree()
        self.apply_ui_theme()

        self.root.title("Pomodoro App — Sessions")
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    Pomodoro(root).main()
