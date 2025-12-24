import tkinter as tk
from tkinter import ttk
import json
import os
import time


class Pomodoro:
    def __init__(self, root,
                 configFile="config.json",
                 sessionsFile="sessions.json",
                 statsFile="stats.json"):

        self.root = root
        self.configFile = configFile
        self.sessionsFile = sessionsFile
        self.statsFile = statsFile

        # ---------------- TIMER STATE ----------------
        self.totalSeconds = 0
        self.initialSeconds = 0
        self.timerRunning = False
        self.currentJob = None
        self.current_phase = "work"
        self.current_cycle = 0
        self.target_cycles = 0
        self.session_start_time = None

        # ---------------- UI STATE ----------------
        self.dark_mode = False
        self.timeString = tk.StringVar(value="00:00")

        # ---------------- DATA ----------------
        self.sessions = self.load_sessions()
        self.stats = self.load_stats()

        # ---------------- UI REFS ----------------
        self.sessionTree = None
        self.pauseButton = None
        self.progress = None
        self.style = ttk.Style()

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

        try:
            with open(self.sessionsFile, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def save_sessions(self):
        with open(self.sessionsFile, "w") as f:
            json.dump(self.sessions, f, indent=2)

    def load_stats(self):
        if not os.path.exists(self.statsFile):
            data = {
                "total_focus_minutes": 0,
                "completed_sessions": 0
            }
            with open(self.statsFile, "w") as f:
                json.dump(data, f, indent=2)
            return data

        try:
            with open(self.statsFile, "r") as f:
                return json.load(f)
        except Exception:
            return {"total_focus_minutes": 0, "completed_sessions": 0}

    def save_stats(self):
        with open(self.statsFile, "w") as f:
            json.dump(self.stats, f, indent=2)

    # ======================================================
    # TREEVIEW
    # ======================================================

    def refresh_tree(self):
        self.sessionTree.delete(*self.sessionTree.get_children())

        for i, s in enumerate(self.sessions):
            tag = f"row{i % 10}"
            self.sessionTree.insert(
                "", "end", iid=str(i),
                values=(s["name"], s["work"], s["break"], s["cycles"]),
                tags=(tag,)
            )

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

        def save(_=None):
            self.sessionTree.set(row, col, entry.get())
            entry.destroy()
            self.sync_tree_to_sessions()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def selected_index(self):
        sel = self.sessionTree.selection()
        return int(sel[0]) if sel else None

    # ======================================================
    # TIMER CORE (FIXED)
    # ======================================================

    def cancel_timer_job(self):
        if self.currentJob:
            self.root.after_cancel(self.currentJob)
            self.currentJob = None

    def start_selected(self):
        idx = self.selected_index()
        if idx is None:
            return

        s = self.sessions[idx]
        self.current_cycle = 1
        self.target_cycles = s["cycles"]
        self.current_phase = "work"
        self.totalSeconds = s["work"] * 60
        self.initialSeconds = self.totalSeconds
        self.session_start_time = time.time()

        self.timerRunning = True
        self.update_time()
        self.run_timer()

    def run_timer(self):
        if not self.timerRunning:
            return

        if self.totalSeconds > 0:
            self.totalSeconds -= 1
            self.update_time()
            self.progress["value"] = 100 * (1 - self.totalSeconds / self.initialSeconds)
            self.currentJob = self.root.after(1000, self.run_timer)
        else:
            idx = self.selected_index()
            if idx is None:
                return

            s = self.sessions[idx]

            if self.current_phase == "work":
                self.current_phase = "break"
                self.totalSeconds = s["break"] * 60
            else:
                if self.current_cycle < self.target_cycles:
                    self.current_cycle += 1
                    self.current_phase = "work"
                    self.totalSeconds = s["work"] * 60
                else:
                    self.finish_session()
                    return

            self.initialSeconds = max(self.totalSeconds, 1)
            self.run_timer()

    def finish_session(self):
        self.timerRunning = False
        elapsed = int((time.time() - self.session_start_time) / 60)

        self.stats["total_focus_minutes"] += elapsed
        self.stats["completed_sessions"] += 1
        self.save_stats()

        self.timeString.set("Finished")
        self.progress["value"] = 100

    def pause_resume(self):
        self.timerRunning = not self.timerRunning
        self.pauseButton.config(text="Resume" if not self.timerRunning else "Pause")

        if self.timerRunning:
            self.run_timer()
        else:
            self.cancel_timer_job()

    def stop_timer(self):
        self.timerRunning = False
        self.cancel_timer_job()
        self.timeString.set("00:00")
        self.progress["value"] = 0

    def update_time(self):
        m, s = divmod(self.totalSeconds, 60)
        self.timeString.set(f"{m:02d}:{s:02d}")

    # ======================================================
    # THEME SYSTEM (SAFE)
    # ======================================================

    def toggle_theme(self):
        was_running = self.timerRunning
        self.timerRunning = False
        self.cancel_timer_job()

        self.dark_mode = not self.dark_mode
        self.apply_theme()

        if was_running:
            self.timerRunning = True
            self.run_timer()

    def apply_theme(self):
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "#ffffff" if self.dark_mode else "#000000"

        self.root.configure(bg=bg)

        self.style.theme_use("clam")
        self.style.configure("Treeview",
                              background=bg,
                              foreground=fg,
                              fieldbackground=bg,
                              rowheight=26)

        self.style.map("Treeview",
                       background=[("selected", "#007acc")])

        light_rows = [
            "#ffffff", "#f2f2f2", "#e8f4ff", "#fff4e6", "#e6ffe6",
            "#f9e6ff", "#ffe6e6", "#e6f9ff", "#f0ffe6", "#f7f7d9"
        ]

        dark_rows = [
            "#2a2a2a", "#333333", "#003b5c", "#5c3b00", "#004d1a",
            "#3d004d", "#4d0000", "#003d4d", "#3d4d00", "#4d4d1a"
        ]

        colors = dark_rows if self.dark_mode else light_rows

        for i, c in enumerate(colors):
            self.sessionTree.tag_configure(f"row{i}", background=c)

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
            self.sessionTree.column(c, width=100, anchor="center")

        self.sessionTree.column("name", width=220, anchor="w")
        self.sessionTree.pack()
        self.sessionTree.bind("<Double-1>", self.edit_cell)

        btns = tk.Frame(left)
        btns.pack(pady=5)

        tk.Button(btns, text="Add", width=6,
                  command=lambda: (self.sessions.append(
                      {"name": "New Session", "work": 25, "break": 5, "cycles": 4}),
                                   self.refresh_tree())).grid(row=0, column=0, padx=2)

        tk.Button(btns, text="Remove", width=6,
                  command=lambda: (self.sessions.pop(self.selected_index())
                                   if self.selected_index() is not None else None,
                                   self.refresh_tree())).grid(row=0, column=1, padx=2)

        tk.Button(btns, text="Save", width=6,
                  command=self.save_sessions).grid(row=0, column=2, padx=2)

        tk.Label(right, textvariable=self.timeString,
                 font=("Arial", 36, "bold")).pack(pady=20)

        self.progress = ttk.Progressbar(right, length=300)
        self.progress.pack(pady=10)

        ctrl = tk.Frame(right)
        ctrl.pack(pady=10)

        tk.Button(ctrl, text="Start Selected",
                  command=self.start_selected).grid(row=0, column=0, padx=5)

        self.pauseButton = tk.Button(ctrl, text="Pause",
                                     command=self.pause_resume)
        self.pauseButton.grid(row=0, column=1, padx=5)

        tk.Button(ctrl, text="Stop",
                  command=self.stop_timer).grid(row=0, column=2, padx=5)

        tk.Button(right, text="Toggle Theme",
                  command=self.toggle_theme).pack(pady=5)

        self.refresh_tree()
        self.apply_theme()

        self.root.title("Pomodoro App — Sessions")
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    Pomodoro(root).main()
