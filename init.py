import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import time
import json
import os


class Pomodoro:
    def __init__(self, root, configFile='config.json', sessionsFile='sessions.json'):
        self.root = root
        self.configFile = configFile
        self.sessionsFile = sessionsFile
        self.configData = self.LoadConfig(configFile)

        # Timer states
        self.totalSeconds = 25 * 60
        self.timerRunning = False
        self.currentJob = None
        self.current_phase = 'work'  # or 'break'
        self.current_cycle = 0
        self.target_cycles = 0

        # Sessions (list of dicts)
        self.sessions = self.LoadSessions(sessionsFile)

        # UI elements placeholders
        self.timeString = None
        self.timerLabel = None
        self.sessionTree = None

    def LoadConfig(self, configFile):
        if not os.path.exists(configFile):
            # Default font and colors
            return {
                "timer_font": {"family": "arial", "size": 28, "style": "bold"},
                "colors": {"text_fg": "black"}
            }
        try:
            with open(configFile, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                "timer_font": {"family": "arial", "size": 28, "style": "bold"},
                "colors": {"text_fg": "black"}
            }

    def LoadSessions(self, sessionsFile):
        if not os.path.exists(sessionsFile):
            # Create sensible defaults
            default = [
                {"name": "Pomodoro (25/5)", "work": 25, "break": 5, "cycles": 4},
                {"name": "Short Sprint (15/3)", "work": 15, "break": 3, "cycles": 4},
                {"name": "Long Focus (50/10)", "work": 50, "break": 10, "cycles": 2}
            ]
            try:
                with open(sessionsFile, 'w') as f:
                    json.dump(default, f, indent=2)
            except Exception:
                pass
            return default

        try:
            with open(sessionsFile, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def SaveSessions(self):
        try:
            with open(self.sessionsFile, 'w') as f:
                json.dump(self.sessions, f, indent=2)
            messagebox.showinfo("Saved", f"Sessions saved to {self.sessionsFile}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save sessions: {e}")

    def refresh_session_list(self):
        # clear existing rows
        for iid in self.sessionTree.get_children():
            self.sessionTree.delete(iid)
        # insert rows with stable iids matching their index
        for i, s in enumerate(self.sessions):
            self.sessionTree.insert('', 'end', iid=str(i), values=(s.get('name',''), s.get('work',0), s.get('break',0), s.get('cycles',1)))

    def prompt_session(self, existing=None):
        # existing: dict or None
        name = simpledialog.askstring("Name", "Session name:", initialvalue=(existing.get('name') if existing else ''))
        if not name:
            return None
        try:
            work = int(simpledialog.askstring("Work Minutes", "Work minutes:", initialvalue=str(existing.get('work',25) if existing else '25')))
            brk = int(simpledialog.askstring("Break Minutes", "Break minutes:", initialvalue=str(existing.get('break',5) if existing else '5')))
            cycles = int(simpledialog.askstring("Cycles", "Number of cycles:", initialvalue=str(existing.get('cycles',4) if existing else '4')))
        except Exception:
            messagebox.showerror("Invalid", "Please enter valid integer values for minutes and cycles.")
            return None
        return {"name": name, "work": work, "break": brk, "cycles": cycles}

    def add_session(self):
        s = self.prompt_session()
        if s:
            self.sessions.append(s)
            self.refresh_session_list()

    def edit_session(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showinfo("Select", "Please select a session to edit.")
            return
        s = self.prompt_session(existing=self.sessions[idx])
        if s:
            self.sessions[idx] = s
            self.refresh_session_list()

    def remove_session(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showinfo("Select", "Please select a session to remove.")
            return
        if messagebox.askyesno("Confirm", f"Remove session '{self.sessions[idx]['name']}'?"):
            del self.sessions[idx]
            self.refresh_session_list()

    def move_up(self):
        idx = self.get_selected_index()
        if idx is None or idx == 0:
            return
        self.sessions[idx-1], self.sessions[idx] = self.sessions[idx], self.sessions[idx-1]
        self.refresh_session_list()
        self.select_index(idx-1)

    def move_down(self):
        idx = self.get_selected_index()
        if idx is None or idx >= len(self.sessions)-1:
            return
        self.sessions[idx+1], self.sessions[idx] = self.sessions[idx], self.sessions[idx+1]
        self.refresh_session_list()
        self.select_index(idx+1)

    def get_selected_index(self):
        sel = self.sessionTree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            # fallback to index lookup
            children = list(self.sessionTree.get_children())
            return children.index(sel[0]) if sel[0] in children else None

    def select_index(self, idx):
        children = list(self.sessionTree.get_children())
        if not children:
            return
        if idx < 0:
            idx = 0
        if idx >= len(children):
            idx = len(children) - 1
        iid = str(idx)
        if iid not in children:
            iid = children[idx]
        self.sessionTree.selection_set(iid)
        self.sessionTree.see(iid)

    def StartSelectedSession(self):
        idx = self.get_selected_index()
        if idx is None:
            messagebox.showinfo("Select", "Please select a session to start.")
            return
        s = self.sessions[idx]
        self.current_cycle = 1
        self.target_cycles = max(1, int(s.get('cycles', 1)))
        self.current_phase = 'work'
        self.totalSeconds = int(s.get('work', 25)) * 60
        self.update_time_display()
        self.start_timer_loop()

    def start_timer_loop(self):
        if self.timerRunning:
            return
        self.timerRunning = True
        self.run_countdown()

    def pause_resume(self):
        if self.timerRunning:
            # pause
            if self.currentJob:
                self.root.after_cancel(self.currentJob)
                self.currentJob = None
            self.timerRunning = False
            self.pauseButton.config(text='Resume')
        else:
            # resume
            self.timerRunning = True
            self.pauseButton.config(text='Pause')
            self.run_countdown()

    def stop_timer(self):
        if self.currentJob:
            self.root.after_cancel(self.currentJob)
            self.currentJob = None
        self.timerRunning = False
        self.timeString.set("00:00")
        self.pauseButton.config(text='Pause')

    def run_countdown(self):
        if self.totalSeconds > 0:
            minutes = self.totalSeconds // 60
            seconds = self.totalSeconds % 60
            self.timeString.set(f"{minutes:02d}:{seconds:02d}")
            self.totalSeconds -= 1
            self.currentJob = self.root.after(1000, self.run_countdown)
        else:
            # phase finished
            if self.current_phase == 'work':
                # start break
                idx = self.get_selected_index()
                s = self.sessions[idx] if idx is not None else {'break': 5}
                self.current_phase = 'break'
                self.totalSeconds = int(s.get('break', 5)) * 60
                messagebox.showinfo("Phase", f"Work done — starting break ({s.get('break',5)} minutes)")
                self.run_countdown()
            else:
                # finished break
                if self.current_cycle < self.target_cycles:
                    self.current_cycle += 1
                    idx = self.get_selected_index()
                    s = self.sessions[idx] if idx is not None else {'work': 25}
                    self.current_phase = 'work'
                    self.totalSeconds = int(s.get('work', 25)) * 60
                    messagebox.showinfo("Cycle", f"Starting cycle {self.current_cycle} of {self.target_cycles}")
                    self.run_countdown()
                else:
                    self.timerRunning = False
                    self.timeString.set("Finished")
                    messagebox.showinfo("Done", "All cycles completed!")

    def update_time_display(self):
        minutes = self.totalSeconds // 60
        seconds = self.totalSeconds % 60
        self.timeString.set(f"{minutes:02d}:{seconds:02d}")

    def main(self):
        # Load font config
        fontConfig = self.configData.get("timer_font", {})
        colourConfig = self.configData.get("colors", {})

        timerFont = (fontConfig.get("family", "arial"), fontConfig.get("size", 28), fontConfig.get("style", "bold"))
        textColour = colourConfig.get("text_fg", "black")

        # Layout: left = sessions, right = timer
        left = tk.Frame(self.root, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(self.root, padx=10, pady=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(left, text="Sessions", font=("arial", 14, "bold")).pack()
        cols = ('name', 'work', 'break', 'cycles')
        self.sessionTree = ttk.Treeview(left, columns=cols, show='headings', height=12)
        self.sessionTree.heading('name', text='Name')
        self.sessionTree.column('name', width=200, anchor='w')
        self.sessionTree.heading('work', text='Work (m)')
        self.sessionTree.column('work', width=70, anchor='center')
        self.sessionTree.heading('break', text='Break (m)')
        self.sessionTree.column('break', width=70, anchor='center')
        self.sessionTree.heading('cycles', text='Cycles')
        self.sessionTree.column('cycles', width=60, anchor='center')
        self.sessionTree.pack(pady=6, fill=tk.Y)
        self.sessionTree.bind("<Double-1>", lambda e: self.edit_session())

        btnFrame = tk.Frame(left)
        btnFrame.pack(pady=4)

        tk.Button(btnFrame, text="Add", width=6, command=self.add_session).grid(row=0, column=0, padx=2)
        tk.Button(btnFrame, text="Edit", width=6, command=self.edit_session).grid(row=0, column=1, padx=2)
        tk.Button(btnFrame, text="Remove", width=6, command=self.remove_session).grid(row=0, column=2, padx=2)
        tk.Button(btnFrame, text="Save", width=6, command=self.SaveSessions).grid(row=0, column=3, padx=2)

        reorder = tk.Frame(left)
        reorder.pack(pady=4)
        tk.Button(reorder, text="Up", width=6, command=self.move_up).grid(row=0, column=0, padx=2)
        tk.Button(reorder, text="Down", width=6, command=self.move_down).grid(row=0, column=1, padx=2)

        # Timer display
        self.timeString = tk.StringVar(self.root)
        self.timeString.set("00:00")
        self.timerLabel = tk.Label(right, textvariable=self.timeString, font=timerFont, fg=textColour)
        self.timerLabel.pack(pady=20)

        controls = tk.Frame(right)
        controls.pack(pady=6)

        tk.Button(controls, text="Start Selected", command=self.StartSelectedSession, width=14).grid(row=0, column=0, padx=6)
        self.pauseButton = tk.Button(controls, text="Pause", command=self.pause_resume, width=10)
        self.pauseButton.grid(row=0, column=1, padx=6)
        tk.Button(controls, text="Stop", command=self.stop_timer, width=10).grid(row=0, column=2, padx=6)

        note = tk.Label(right, text="Select a session, then start. Add and reorder sessions to your preference.", font=("arial", 9), fg="gray")
        note.pack(pady=8)

        # populate list
        self.refresh_session_list()

        self.root.title("Pomodoro App — Sessions")
        self.root.mainloop()


if __name__ == '__main__':
    rootWindow = tk.Tk()
    pomo = Pomodoro(rootWindow)
    pomo.main()