import tkinter as tk
from tkinter import ttk, messagebox
import json, os
from datetime import datetime, timedelta

# ================= COLORS =================

ROW_COLORS = [
    "#e8f4ff", "#fff0e6", "#eaffea", "#f5e9ff", "#ffeaea",
    "#f0fff7", "#fffbe6", "#e6f7ff", "#f9e6ff", "#eef2f7"
]

ROW_COLORS_DARK = [
    "#1a5276", "#6e2c00", "#1e8449", "#6c3483", "#922b21",
    "#117a65", "#7d6608", "#1f618d", "#76448a", "#2c3e50"
]

# ================= APP =================

class Pomodoro:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro App — Task Tracker")

        self.sessionsFile = "sessions.json"
        self.statsFile = "stats.json"
        self.historyFile = "history.json"

        # Timer state
        self.totalSeconds = 0
        self.phase_total = 0
        self.timerRunning = False
        self.paused = False
        self.currentJob = None

        self.current_row = None
        self.current_cycle = 1
        self.current_phase = "work"

        # UI state
        self.dark_mode = False
        self.color_offset = 0

        self.timeString = tk.StringVar(value="00:00")
        self.progressValue = tk.IntVar(value=0)

        self.sessions = self.safe_load_json(self.sessionsFile, [])
        self.stats = self.safe_load_json(self.statsFile, {
            "work_minutes_today": 0,
            "sessions_completed": 0,
            "last_active_date": "",
            "current_streak": 0,
            "theme": "light"
        })
        self.history = self.safe_load_json(self.historyFile, [])

        if self.stats.get("theme") == "dark":
            self.dark_mode = True

        self.build_ui()
        self.apply_ui_theme()
        self.refresh_tree()
        self.update_stats_label()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ================= SAFE JSON =================

    def safe_load_json(self, path, default):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w") as f:
                json.dump(default, f, indent=2)
            return default
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showwarning("JSON Error", f"Corrupted {path} — resetting to default.")
            with open(path, "w") as f:
                json.dump(default, f, indent=2)
            return default

    # ================= TREEVIEW =================

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(self.sessions):
            color = (ROW_COLORS_DARK if self.dark_mode else ROW_COLORS)[
                (i + self.color_offset) % 10
            ]
            self.tree.insert(
                "", "end", iid=str(i),
                values=(s["name"], s["Task Duration"], s["break"], s["cycles"]),
                tags=(f"row{i}",)
            )
            self.tree.tag_configure(f"row{i}", background=color)

    def sync_tree_to_sessions(self):
        self.sessions.clear()
        for iid in self.tree.get_children():
            n, w, b, c = self.tree.item(iid, "values")
            try:
                w_int = int(w) if w.strip() != "" else 25
            except ValueError:
                w_int = 25
            try:
                b_int = int(b) if b.strip() != "" else 5
            except ValueError:
                b_int = 5
            try:
                c_int = int(c) if c.strip() != "" else 1
            except ValueError:
                c_int = 1

            self.sessions.append({
                "name": n or "Unnamed Task",
                "Task Duration": w_int,
                "break": b_int,
                "cycles": c_int
            })
        with open(self.sessionsFile, "w") as f:
            json.dump(self.sessions, f, indent=2)

    # ================= CELL EDITING WITH NUMERIC VALIDATION =================

    def edit_cell(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row or col == "#0":
            return

        col_index = int(col.replace("#", "")) - 1
        x, y, w, h = self.tree.bbox(row, col)
        value = self.tree.set(row, col)

        if col_index in (1, 2, 3):  # Numeric columns: Task Duration, Break, Cycles
            entry = tk.Entry(self.tree, validate="key")
            vcmd = (entry.register(self.validate_numeric_input), "%P")
            entry.config(validatecommand=vcmd)
        else:  # Task Name: free text
            entry = tk.Entry(self.tree)

        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, value)
        entry.focus()

        def save(_=None):
            new_val = entry.get()
            # For numeric fields, prevent saving empty string
            if col_index in (1, 2, 3) and new_val == "":
                new_val = "0"
            self.tree.set(row, col, new_val)
            entry.destroy()
            self.sync_tree_to_sessions()

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", save)

    def validate_numeric_input(self, value_if_allowed):
        """Allow only digits (and empty during typing)"""
        if value_if_allowed == "":
            return True
        return value_if_allowed.isdigit()

    # ================= TASK BUTTONS =================

    def add_task(self):
        self.sessions.append({
            "name": "New Task",
            "Task Duration": 25,
            "break": 5,
            "cycles": 1
        })
        self.refresh_tree()
        self.sync_tree_to_sessions()

    def remove_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        del self.sessions[idx]
        self.refresh_tree()
        self.sync_tree_to_sessions()
        self.current_row = None

    def cycle_row_colors(self):
        self.color_offset = (self.color_offset + 1) % 10
        self.refresh_tree()

    # ================= TIMER =================

    def update_time(self):
        m, s = divmod(self.totalSeconds, 60)
        self.timeString.set(f"{m:02d}:{s:02d}")

    def start_selected(self):
        if self.timerRunning:
            return
        sel = self.tree.selection()
        if not sel:
            return
        self.current_row = int(sel[0])
        self.current_cycle = 1
        self.current_phase = "work"
        self.start_phase()

    def start_phase(self):
        if self.current_row is None or self.current_row >= len(self.sessions):
            self.timerRunning = False
            self.timeString.set("❌ Invalid task")
            self.root.after(2000, lambda: self.timeString.set("00:00"))
            return

        task = self.sessions[self.current_row]
        self.phase_total = (task["Task Duration"] if self.current_phase == "work" else task["break"]) * 60
        self.totalSeconds = self.phase_total
        self.progressValue.set(0)
        self.timerRunning = True
        self.paused = False
        self.update_time()
        self.run_timer()
        self.update_paused_label()  # Hide "Paused"

    def run_timer(self):
        if not self.timerRunning or self.paused:
            return
        if self.totalSeconds > 0:
            self.totalSeconds -= 1
            self.update_time()
            self.draw_progress_bar(int(((self.phase_total - self.totalSeconds) / self.phase_total) * 100))
            self.currentJob = self.root.after(1000, self.run_timer)
        else:
            self.finish_cycle()

    def finish_cycle(self):
        self.timerRunning = False
        self.timeString.set("Task Done")
        self.record_session_completion()
        self.root.after(15000, self.start_next_task)

    def record_session_completion(self):
        # ✅ CRASH FIX: Validate current_row
        if self.current_row is None or self.current_row >= len(self.sessions):
            return

        task = self.sessions[self.current_row]
        duration = task["Task Duration"]
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        last_date = self.stats.get("last_active_date", "")
        self.stats["work_minutes_today"] += duration
        self.stats["sessions_completed"] += 1

        if last_date == today_str:
            pass
        elif last_date == "":
            self.stats["current_streak"] = 1
        else:
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            if last_date == yesterday:
                self.stats["current_streak"] += 1
            else:
                self.stats["current_streak"] = 1
        self.stats["last_active_date"] = today_str
        self.stats["theme"] = "dark" if self.dark_mode else "light"

        self.history.append({
            "timestamp": now.isoformat(),
            "task_name": task["name"],
            "duration_minutes": duration
        })

        with open(self.statsFile, "w") as f:
            json.dump(self.stats, f, indent=2)
        with open(self.historyFile, "w") as f:
            json.dump(self.history, f, indent=2)

        self.update_stats_label()

    def start_next_task(self):
        # ✅ CRASH FIX
        if self.current_row is None:
            self.timeString.set("🎉 All done!")
            return
        nxt = self.current_row + 1
        if nxt < len(self.sessions):
            self.tree.selection_set(str(nxt))
            self.current_row = nxt
            self.start_phase()
        else:
            self.timeString.set("🎉 Congratulations! All tasks completed!")

    def pause_resume(self):
        if not self.timerRunning:
            return
        self.paused = not self.paused
        self.pauseBtn.config(text="Resume" if self.paused else "Pause")
        self.update_paused_label()
        if not self.paused:
            self.run_timer()

    def stop_timer(self):
        self.timerRunning = False
        self.paused = False
        self.timeString.set("00:00")
        self.progressValue.set(0)
        self.draw_progress_bar(0)
        self.update_paused_label()  # Hide "Paused"

    def update_paused_label(self):
        """Show or hide the 'Paused' indicator with background box"""
        if self.paused:
            bg_color = "#fff2cc" if not self.dark_mode else "#332a00"
            text_color = "#ff9900" if not self.dark_mode else "#ffcc00"
            self.pausedCanvas.config(bg=bg_color)
            self.pausedCanvas.itemconfig(self.pausedText, text="⏸️ Paused", fill=text_color)
        else:
            bg_color = "#f0f0f0" if not self.dark_mode else "#1e1e1e"
            self.pausedCanvas.config(bg=bg_color)
            self.pausedCanvas.itemconfig(self.pausedText, text="")

    # ================= STATS & HISTORY WINDOW =================

    def show_history_window(self):
        win = tk.Toplevel(self.root)
        win.title("📊 Pomodoro History")
        win.geometry("600x500")
        win.transient(self.root)
        win.grab_set()

        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "#ffffff" if self.dark_mode else "#000000"
        win.configure(bg=bg)

        tk.Label(win, text="📊 Pomodoro History", font=("Arial", 16, "bold"), bg=bg, fg=fg).pack(pady=10)

        tab_frame = tk.Frame(win, bg=bg)
        tab_frame.pack(pady=5)

        # Text area for history
        text_area = tk.Text(win, wrap=tk.WORD, font=("Consolas", 10), bg="#2d2d2d" if self.dark_mode else "#ffffff", fg=fg, height=20)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Button(tab_frame, text="Daily", command=lambda: self.render_history_view("daily", text_area)).pack(side=tk.LEFT, padx=5)
        tk.Button(tab_frame, text="Monthly", command=lambda: self.render_history_view("monthly", text_area)).pack(side=tk.LEFT, padx=5)
        tk.Button(tab_frame, text="Yearly", command=lambda: self.render_history_view("yearly", text_area)).pack(side=tk.LEFT, padx=5)

        clear_btn = tk.Button(win, text="🧹 Clear History", command=lambda: self.clear_history(text_area), bg="#ff4444", fg="white")
        clear_btn.pack(pady=5)

        self.render_history_view("daily", text_area)

    def render_history_view(self, view_type, text_area):
        text_area.config(state=tk.NORMAL)
        text_area.delete(1.0, tk.END)

        now = datetime.now()
        history_by_key = {}

        for entry in self.history:
            ts = datetime.fromisoformat(entry["timestamp"])
            if view_type == "daily":
                key = ts.strftime("%Y-%m-%d")
            elif view_type == "monthly":
                key = ts.strftime("%Y-%m")
            elif view_type == "yearly":
                key = ts.strftime("%Y")
            else:
                key = "All"

            if key not in history_by_key:
                history_by_key[key] = []
            history_by_key[key].append(entry)

        for key in sorted(history_by_key.keys(), reverse=True):
            total_minutes = sum(e["duration_minutes"] for e in history_by_key[key])
            if view_type == "daily":
                label = f"📅 {key} → {total_minutes} min"
            elif view_type == "monthly":
                label = f"📆 {key} → {total_minutes} min"
            else:
                label = f"🗓️ {key} → {total_minutes} min"
            text_area.insert(tk.END, label + "\n")
            for e in history_by_key[key]:
                time_str = datetime.fromisoformat(e["timestamp"]).strftime("%H:%M")
                text_area.insert(tk.END, f"   • {e['task_name']} ({e['duration_minutes']} min) at {time_str}\n")
            text_area.insert(tk.END, "\n")

        text_area.config(state=tk.DISABLED)

    def clear_history(self, text_area):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all history? This cannot be undone."):
            self.history.clear()
            with open(self.historyFile, "w") as f:
                json.dump(self.history, f, indent=2)
            self.render_history_view("daily", text_area)
            messagebox.showinfo("Cleared", "History cleared successfully!")

    # ================= UI =================

    def draw_progress_bar(self, percent):
        self.canvas.delete("all")
        w, h = 320, 20
        fill = "#e040fb" if self.dark_mode else "#4caf50"
        bg = "#2d2d2d" if self.dark_mode else "#e0e0e0"
        self.canvas.config(bg=bg)
        self.canvas.create_rectangle(0, 0, w, h, fill=bg, outline=bg)
        self.canvas.create_rectangle(0, 0, int(w * percent / 100), h, fill=fill, outline=fill)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_ui_theme()

    def apply_ui_theme(self):
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "#ffffff" if self.dark_mode else "#000000"
        self.root.configure(bg=bg)
        for f in (self.left, self.right, self.ctrl, self.btns):
            f.configure(bg=bg)
        self.timerLabel.configure(bg=bg, fg=fg)
        self.statsLabel.configure(bg=bg, fg=fg)
        self.pausedCanvas.config(bg=bg)  # ← NEW
        self.refresh_tree()
        self.draw_progress_bar(self.progressValue.get())
        self.update_paused_label()  # ← NEW

    # ================= BUILD UI =================

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
        for col, w in zip(self.tree["columns"], (160, 120, 80, 80)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.column("Task Name", anchor="w")
        self.tree.pack()
        self.tree.bind("<Double-1>", self.edit_cell)

        self.btns = tk.Frame(self.left)
        self.btns.pack(pady=6)
        tk.Button(self.btns, text="Add", command=self.add_task).grid(row=0, column=0, padx=3)
        tk.Button(self.btns, text="Remove", command=self.remove_task).grid(row=0, column=1, padx=3)
        tk.Button(self.btns, text="Row Colours", command=self.cycle_row_colors).grid(row=0, column=2, padx=3)
        tk.Button(self.btns, text="History", command=self.show_history_window).grid(row=0, column=3, padx=3)
        tk.Button(self.btns, text="Save Now", command=self.sync_tree_to_sessions).grid(row=0, column=4, padx=3)

        # ✅ PAUSED BOX — NEW
        self.pausedCanvas = tk.Canvas(self.right, width=100, height=30, bg="#f0f0f0", highlightthickness=0)
        self.pausedCanvas.pack(pady=5)

        self.pausedText = self.pausedCanvas.create_text(
            50, 15,
            text="",
            font=("Arial", 12, "bold"),
            fill="#ff9900"
        )

        self.timerLabel = tk.Label(self.right, textvariable=self.timeString, font=("Arial", 32, "bold"))
        self.timerLabel.pack(pady=10)

        self.statsLabel = tk.Label(self.right, font=("Arial", 10))
        self.statsLabel.pack(pady=5)

        self.canvas = tk.Canvas(self.right, width=320, height=20, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.ctrl = tk.Frame(self.right)
        self.ctrl.pack(pady=10)
        tk.Button(self.ctrl, text="Start", command=self.start_selected).grid(row=0, column=0, padx=5)
        self.pauseBtn = tk.Button(self.ctrl, text="Pause", command=self.pause_resume)
        self.pauseBtn.grid(row=0, column=1, padx=5)
        tk.Button(self.ctrl, text="Stop", command=self.stop_timer).grid(row=0, column=2, padx=5)
        tk.Button(self.ctrl, text="No Blue Ray Light pls", command=self.toggle_dark_mode).grid(row=0, column=3, padx=5)

    def update_stats_label(self):
        s = self.stats
        self.statsLabel.config(
            text=f"Today: {s['work_minutes_today']} min | Sessions: {s['sessions_completed']} | Streak: {s['current_streak']}",
            fg="#ffffff" if self.dark_mode else "#000000"
        )

    def on_closing(self):
        with open(self.sessionsFile, "w") as f:
            json.dump(self.sessions, f, indent=2)
        with open(self.statsFile, "w") as f:
            json.dump(self.stats, f, indent=2)
        with open(self.historyFile, "w") as f:
            json.dump(self.history, f, indent=2)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    Pomodoro(root)
    root.mainloop()