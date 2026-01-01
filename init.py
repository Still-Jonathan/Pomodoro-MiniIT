import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime, timedelta

ROW_COLORS = [
    "#e8f4ff", "#fff0e6", "#eaffea", "#f5e9ff", "#ffeaea",
    "#f0fff7", "#fffbe6", "#e6f7ff", "#f9e6ff", "#eef2f7"
]

ROW_COLORS_DARK = [
    "#1a5276",  # deep blue
    "#6e2c00",  # rich brown
    "#1e8449",  # forest green
    "#6c3483",  # deep purple
    "#922b21",  # crimson red
    "#17a589",  # teal
    "#f1c40f",  # golden yellow
    "#2980b9",  # bright blue
    "#9b59b6",  # magenta
    "#34495e"   # slate gray
]


class Pomodoro:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro App — Task Tracker")

        self.sessionsFile = "sessions.json"
        self.statsFile = "stats.json"

        # timer state
        self.totalSeconds = 0
        self.phase_total = 0
        self.timerRunning = False
        self.paused = False
        self.currentJob = None

        self.current_row = None
        self.current_cycle = 1
        self.current_phase = "work"  # work / break

        # UI state
        self.dark_mode = False
        self.color_offset = 0

        self.timeString = tk.StringVar(value="00:00")
        self.progressValue = tk.IntVar(value=0)

        self.sessions = self.load_sessions()
        self.stats = self.load_stats()

        # Apply saved theme on startup
        if self.stats.get("theme") == "dark":
            self.dark_mode = True

        self.build_ui()
        self.apply_ui_theme()
        self.refresh_tree()

        # Auto-save on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------- DATA ----------

    def load_sessions(self):
        if not os.path.exists(self.sessionsFile):
            data = [
                {"name": "Task 1", "Task Duration": 25, "break": 5, "cycles": 2},
                {"name": "Task 2", "Task Duration": 15, "break": 3, "cycles": 2},
            ]
            with open(self.sessionsFile, "w") as f:
                json.dump(data, f, indent=2)
            return data
        with open(self.sessionsFile, "r") as f:
            return json.load(f)

    def save_sessions(self):
        with open(self.sessionsFile, "w") as f:
            json.dump(self.sessions, f, indent=2)

    def load_stats(self):
        if not os.path.exists(self.statsFile):
            default_stats = {
                "work_minutes_today": 0,
                "sessions_completed": 0,
                "last_active_date": "",
                "current_streak": 0,
                "theme": "light"
            }
            self.save_stats(default_stats)
            return default_stats
        with open(self.statsFile, "r") as f:
            return json.load(f)

    def save_stats(self, stats=None):
        if stats is None:
            stats = self.stats
        with open(self.statsFile, "w") as f:
            json.dump(stats, f, indent=2)

    # ---------- TREEVIEW ----------

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(self.sessions):
            tag = f"row{i}"
            color = ROW_COLORS_DARK[(i + self.color_offset) % len(ROW_COLORS_DARK)] if self.dark_mode else ROW_COLORS[(i + self.color_offset) % len(ROW_COLORS)]
            self.tree.insert("", "end", iid=str(i), values=(s["name"], s["Task Duration"], s["break"], s["cycles"]), tags=(tag,))
            self.tree.tag_configure(tag, background=color)

    def sync_tree_to_sessions(self):
        self.sessions.clear()
        for iid in self.tree.get_children():
            name, work, brk, cyc = self.tree.item(iid, "values")
            self.sessions.append({"name": name, "Task Duration": int(work), "break": int(brk), "cycles": int(cyc)})
        self.save_sessions()

    def edit_cell(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row or col == "#0":
            return

        col_index = int(col.replace("#", "")) - 1
        if col_index not in (1, 2, 3):
            return self.edit_text_cell(event)

        x, y, w, h = self.tree.bbox(row, col)
        value = self.tree.set(row, col)

        entry = tk.Entry(self.tree, validate="key")
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, value)
        entry.focus()

        vcmd = (entry.register(self.validate_numeric_input), "%P")
        entry.config(validatecommand=vcmd)

        def save(_=None):
            new_val = entry.get() or "0"
            self.tree.set(row, col, new_val)
            entry.destroy()
            self.sync_tree_to_sessions()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def edit_text_cell(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        x, y, w, h = self.tree.bbox(row, col)
        value = self.tree.set(row, col)

        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, value)
        entry.focus()

        def save(_=None):
            self.tree.set(row, col, entry.get())
            entry.destroy()
            self.sync_tree_to_sessions()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def validate_numeric_input(self, value_if_allowed):
        return value_if_allowed == "" or value_if_allowed.isdigit()

    def selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    # ---------- TASK BUTTONS ----------

    def add_task(self):
        self.sessions.append({"name": "New Task", "Task Duration": 25, "break": 5, "cycles": 1})
        self.refresh_tree()
        self.save_sessions()

    def remove_task(self):
        idx = self.selected_index()
        if idx is None:
            return
        del self.sessions[idx]
        self.refresh_tree()
        self.save_sessions()

    def cycle_row_colors(self):
        self.color_offset = (self.color_offset + 1) % len(ROW_COLORS)
        self.refresh_tree()

    # ---------- TIMER ----------

    def start_selected(self):
        if self.timerRunning:  # Prevent spam
            return
        idx = self.selected_index()
        if idx is None:
            return
        self.current_row = idx
        self.current_cycle = 1
        self.current_phase = "work"
        self.start_phase()

    def start_phase(self):
        task = self.sessions[self.current_row]
        self.phase_total = (task["Task Duration"] if self.current_phase == "work" else task["break"]) * 60
        self.totalSeconds = self.phase_total
        self.progressValue.set(0)
        self.timerRunning = True
        self.paused = False
        self.update_time()
        self.run_timer()

    def run_timer(self):
        if not self.timerRunning or self.paused:
            return
        if self.totalSeconds > 0:
            self.totalSeconds -= 1
            self.update_time()
            progress = int(((self.phase_total - self.totalSeconds) / self.phase_total) * 100)
            self.progressValue.set(progress)
            self.draw_progress_bar(progress)
            self.currentJob = self.root.after(1000, self.run_timer)
        else:
            self.advance_phase()

    def advance_phase(self):
        task = self.sessions[self.current_row]
        if self.current_phase == "work":
            if task["break"] > 0:
                self.current_phase = "break"
                self.start_phase()
            else:
                self.finish_cycle()
        else:
            self.finish_cycle()

    def finish_cycle(self):
        task = self.sessions[self.current_row]
        if self.current_cycle < task["cycles"]:
            self.current_cycle += 1
            self.current_phase = "work"
            self.start_phase()
        else:
            self.timerRunning = False
            self.timeString.set("Task Done")
            self.update_session_stats(task["Task Duration"])
            self.root.after(15000, self.start_next_task)

    def update_session_stats(self, task_duration_minutes):
        today = datetime.now().strftime("%Y-%m-%d")
        last_date = self.stats.get("last_active_date", "")
        self.stats["work_minutes_today"] += task_duration_minutes
        self.stats["sessions_completed"] += 1
        if last_date == today:
            pass
        elif last_date == "":
            self.stats["current_streak"] = 1
        else:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            self.stats["current_streak"] = self.stats["current_streak"] + 1 if last_date == yesterday else 1
        self.stats["last_active_date"] = today
        self.stats["theme"] = "dark" if self.dark_mode else "light"
        self.save_stats()
        self.update_stats_label()

    def update_stats_label(self):
        s = self.stats
        self.statsLabel.config(text=f"Today: {s['work_minutes_today']} min | Sessions: {s['sessions_completed']} | Streak: {s['current_streak']}")

    def start_next_task(self):
        next_row = self.current_row + 1
        if next_row < len(self.sessions):
            self.tree.selection_set(str(next_row))
            self.current_row = next_row
            self.current_cycle = 1
            self.current_phase = "work"
            self.start_phase()
        else:
            self.timeString.set("🎉 Congratulations! All tasks completed!")

    def pause_resume(self):
        if not self.timerRunning:
            return
        self.paused = not self.paused
        self.pauseBtn.config(text="Resume" if self.paused else "Pause")
        if not self.paused:
            self.run_timer()

    def stop_timer(self):
        self.timerRunning = False
        self.paused = False
        self.progressValue.set(0)
        self.timeString.set("00:00")
        self.pauseBtn.config(text="Pause")
        self.draw_progress_bar(0)

    def update_time(self):
        m, s = divmod(self.totalSeconds, 60)
        self.timeString.set(f"{m:02d}:{s:02d}")

    # ---------- CUSTOM PROGRESS BAR ----------

    def draw_progress_bar(self, percent):
        # Use the actual canvas size so behavior adapts if changed
        try:
            width = int(self.canvas.cget("width"))
            height = int(self.canvas.cget("height"))
        except Exception:
            width, height = 320, 20

        fill_width = int((percent / 100) * width)
        self.canvas.delete("all")

        trough = "#2d2d2d" if self.dark_mode else "#e0e0e0"
        fill = "#e040fb" if self.dark_mode else "#4caf50"
        highlight = "#f387ff" if self.dark_mode else "#81c784"
        shadow = "#c729e6" if self.dark_mode else "#388e3c"

        # Make canvas background match the trough to avoid any 1px seams
        self.canvas.config(bg=trough)

        # Draw trough (full width) with matching outline to avoid border artifacts
        self.canvas.create_rectangle(0, 0, width, height, fill=trough, outline=trough)

        if fill_width > 0:
            # Ensure at least a single pixel is drawn for small percentages
            fw = max(1, min(fill_width, width))
            self.canvas.create_rectangle(0, 0, fw, height, fill=fill, outline=fill)

            # Draw subtle highlights/shadows only when there is room
            if fw > 2:
                # Top highlight
                self.canvas.create_line(0, 0, fw, 0, fill=highlight, width=1)
                # Bottom shadow
                self.canvas.create_line(0, height - 1, fw, height - 1, fill=shadow, width=1)
                # Right-edge shadow only. Avoid drawing a left-edge vertical highlight
                # which can produce a visible thin line on some platforms/themes
                self.canvas.create_line(fw - 1, 0, fw - 1, height, fill=shadow, width=1)

    # ---------- DARK MODE ----------

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_ui_theme()

    def apply_ui_theme(self):
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "#ffffff" if self.dark_mode else "#000000"
        self.root.configure(bg=bg)
        for frame in (self.left, self.right, self.ctrl, self.btns):
            frame.configure(bg=bg)
        self.timerLabel.configure(bg=bg, fg=fg)
        self.refresh_tree()
        self.draw_progress_bar(self.progressValue.get())
        self.statsLabel.config(bg=bg, fg=fg)

    # ---------- EXIT ----------

    def on_closing(self):
        self.save_sessions()
        self.save_stats()
        self.root.destroy()

    # ---------- UI ----------

    def build_ui(self):
        self.left = tk.Frame(self.root, padx=10, pady=10)
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        self.right = tk.Frame(self.root, padx=20, pady=20)
        self.right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(self.left, text="Task List", font=("Arial", 14, "bold")).pack()

        self.tree = ttk.Treeview(
            self.left,
            columns=("Task Name", "Task Duration", "Break", "Cycles"),
            show="headings",
            height=12
        )
        for col, w in zip(("Task Name", "Task Duration", "Break", "Cycles"), (160, 120, 80, 80)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.column("Task Name", anchor="w")
        self.tree.pack()
        self.tree.bind("<Double-1>", self.edit_cell)

        self.btns = tk.Frame(self.left)
        self.btns.pack(pady=6)
        tk.Button(self.btns, text="Add", width=6, command=self.add_task).grid(row=0, column=0, padx=3)
        tk.Button(self.btns, text="Remove", width=6, command=self.remove_task).grid(row=0, column=1, padx=3)
        tk.Button(self.btns, text="Row Colours", width=10, command=self.cycle_row_colors).grid(row=0, column=2, padx=3)
        tk.Button(self.btns, text="Save Now", width=8, command=self.save_sessions).grid(row=0, column=3, padx=3)

        self.timerLabel = tk.Label(self.right, textvariable=self.timeString, font=("Arial", 32, "bold"))
        self.timerLabel.pack(pady=20)

        self.statsLabel = tk.Label(self.right, text="", font=("Arial", 10), fg="#ffffff" if self.dark_mode else "#000000")
        self.statsLabel.pack(pady=5)

        canvas_bg = "#2d2d2d" if self.dark_mode else "#f0f0f0"
        self.canvas = tk.Canvas(self.right, width=320, height=20, bg=canvas_bg, highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(pady=10)
        self.draw_progress_bar(0)

        self.ctrl = tk.Frame(self.right)
        self.ctrl.pack(pady=10)
        tk.Button(self.ctrl, text="Start", command=self.start_selected).grid(row=0, column=0, padx=5)
        self.pauseBtn = tk.Button(self.ctrl, text="Pause", command=self.pause_resume)
        self.pauseBtn.grid(row=0, column=1, padx=5)
        tk.Button(self.ctrl, text="Stop", command=self.stop_timer).grid(row=0, column=2, padx=5)
        tk.Button(self.ctrl, text="No Blue Ray Light pls", command=self.toggle_dark_mode).grid(row=0, column=3, padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    Pomodoro(root)
    root.mainloop()