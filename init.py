import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import pygame

# Audio Files Configuration
DEFAULT_SOUNDS = {
    "Savana": r"Audio/savana.mp3",
    "Rain": r"Audio/Rain.mp3",
    "Waterfall": r"Audio/waterfall.mp3"
}

THEMES = {
    "savana": {
        "bg": "#EAD7A1",
        "fg": "#3B2F2F",
        "button_bg": "#8D7539",
        "button_fg": "#FFFFFF",
        "progress_trough": "#C8B56A",
        "progress_fill": "#8D7539"
    },
    "water": {
        "bg": "#D0ECF2",
        "fg": "#003B44",
        "button_bg": "#4FA3B5",
        "button_fg": "#FFFFFF",
        "progress_trough": "#A7DCE6",
        "progress_fill": "#4FA3B5"
    },
    "light": {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "button_bg": "#E0E0E0",
        "button_fg": "#000000",
        "progress_trough": "#CCCCCC",
        "progress_fill": "#4CAF50"
    },
    "dark": {
        "bg": "#1E1E1E",
        "fg": "#FFFFFF",
        "button_bg": "#333333",
        "button_fg": "#FFFFFF",
        "progress_trough": "#444444",
        "progress_fill": "#76FF03"
    }
}

# Row colors for different themes
ROW_COLORS_WARM = ["#FFF8DC", "#FFE4B5", "#FFDAB9", "#FFE4C4"]
ROW_COLORS_COOL = ["#E6F3FF", "#D6EAF8", "#C6E0F5", "#B6D7F2"]
ROW_COLORS_LIGHT = ["#F5F5F5", "#EEEEEE", "#E8E8E8", "#E0E0E0"]
ROW_COLORS_DARK = ["#2A2A2A", "#323232", "#3A3A3A", "#424242"]

class Pomodoro:
    def __init__(self, root):
        self.root = root
        self.root.title("Pomodoro App — Task Tracker")

        # Initialize Pygame Mixer
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(0.5)
        except Exception as e:
            print(f"Error initializing audio: {e}")

        self.sessionsFile = "sessions.json"
        self.sessions = self.load_sessions()

        # Custom sounds file
        self.customSoundsFile = "custom_sounds.json"
        self.custom_sounds = self.load_custom_sounds()
        
        # Merge default and custom sounds
        self.sounds = {**DEFAULT_SOUNDS, **self.custom_sounds}

        # timer state
        self.totalSeconds = 0
        self.phase_total = 0
        self.timerRunning = False
        self.paused = False
        self.currentJob = None

        self.current_row = None
        self.current_cycle = 1
        self.current_phase = "work"  # work / break

        # Theme state
        self.current_theme = "light"
        self.current_sound = "Savana"

        self.timeString = tk.StringVar(value="00:00")
        self.progressValue = tk.IntVar(value=0)
        self.volume_var = tk.IntVar(value=50)

        # Task stats
        self.statsFile = "task_stats.json"
        self.stats = self.load_stats()

        self.build_ui()
        self.apply_ui_theme()
        self.refresh_tree()
 
        # Auto-save on window close
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
            return {}
        with open(self.statsFile, "r") as f:
            return json.load(f)
        
    def save_stats(self):
        with open(self.statsFile, "w") as f:
            json.dump(self.stats, f, indent=2)

    def load_custom_sounds(self):
        """Load custom sounds from JSON file"""
        if not os.path.exists(self.customSoundsFile):
            return {}
        try:
            with open(self.customSoundsFile, "r") as f:
                return json.load(f)
        except:
            return {}
    
    def save_custom_sounds(self):
        """Save custom sounds to JSON file"""
        with open(self.customSoundsFile, "w") as f:
            json.dump(self.custom_sounds, f, indent=2)

    # ---------- CUSTOM SOUND MANAGEMENT ----------

    def add_custom_sound(self):
        """Open file dialog to add a custom sound"""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.ogg *.flac"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("OGG Files", "*.ogg"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Get the filename without extension for the default name
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Ask user for a custom name
        name = self.ask_sound_name(base_name)
        if not name:
            return
        
        # Check if name already exists
        if name in self.sounds:
            if not messagebox.askyesno("Name Exists", 
                f"A sound named '{name}' already exists. Do you want to replace it?"):
                return
        
        # Add to custom sounds
        self.custom_sounds[name] = file_path
        self.sounds[name] = file_path
        self.save_custom_sounds()
        
        # Update the dropdown menu
        self.update_sound_menu()
        
        # Select the new sound
        self.sound_var.set(name)
        self.current_sound = name
        
        messagebox.showinfo("Success", f"Sound '{name}' added successfully!")

    def remove_custom_sound(self):
        """Remove a custom sound"""
        current = self.sound_var.get()
        
        # Can't remove default sounds
        if current in DEFAULT_SOUNDS:
            messagebox.showwarning("Cannot Remove", 
                "Default sounds cannot be removed. Only custom sounds can be deleted.")
            return
        
        if current not in self.custom_sounds:
            messagebox.showwarning("Cannot Remove", 
                "Please select a custom sound to remove.")
            return
        
        if messagebox.askyesno("Confirm Removal", 
            f"Are you sure you want to remove '{current}'?"):
            del self.custom_sounds[current]
            del self.sounds[current]
            self.save_custom_sounds()
            
            # Update menu and select a default sound
            self.update_sound_menu()
            self.sound_var.set("Savana")
            self.current_sound = "Savana"
            
            messagebox.showinfo("Removed", f"Sound '{current}' has been removed.")

    def ask_sound_name(self, default_name):
        """Dialog to get custom sound name"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Name Your Sound")
        dialog.geometry("300x120")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter a name for this sound:", 
                 font=("Arial", 10)).pack(pady=10)
        
        name_var = tk.StringVar(value=default_name)
        entry = tk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(pady=5)
        entry.focus()
        entry.select_range(0, tk.END)
        
        result = [None]
        
        def on_ok():
            name = name_var.get().strip()
            if name:
                result[0] = name
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Name", "Please enter a valid name.")
        
        def on_cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())
        
        dialog.wait_window()
        return result[0]

    def update_sound_menu(self):
        """Update the sound dropdown menu with current sounds"""
        menu = self.sound_menu["menu"]
        menu.delete(0, "end")
        
        for sound_name in sorted(self.sounds.keys()):
            menu.add_command(
                label=sound_name,
                command=lambda name=sound_name: self.sound_var.set(name)
            )

    # ---------- AUDIO LOGIC ----------

    def play_music(self):
        """Plays the currently selected sound loop."""
        file_path = self.sounds.get(self.current_sound)
        if file_path and os.path.exists(file_path):
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play(-1)        # Loop indefinitely
            except Exception as e:
                print(f"Error playing music: {e}")
                messagebox.showerror("Playback Error", 
                    f"Could not play '{self.current_sound}'. The file may be corrupt or in an unsupported format.")

    def stop_music(self):
        pygame.mixer.music.stop()

    def pause_music(self):
        pygame.mixer.music.pause()

    def unpause_music(self):
        pygame.mixer.music.unpause()

    def change_music_selection(self, selection):
        self.current_sound = selection
        if self.timerRunning and not self.paused:
            self.play_music()  # Restart with new track if running

    def change_volume(self, value):
        vol = int(value) / 100
        pygame.mixer.music.set_volume(vol)

    # ---------- TREEVIEW ----------

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())

        # Choose row colors based on theme
        if self.current_theme == "savana":
            colours = ROW_COLORS_WARM
        elif self.current_theme == "water":
            colours = ROW_COLORS_COOL
        elif self.current_theme == "light":
            colours = ROW_COLORS_LIGHT
        else:  # dark
            colours = ROW_COLORS_DARK

        for i, s in enumerate(self.sessions):
            tag = f"row{i}"
            colour = colours[i % len(colours)]
            self.tree.insert(
                "", "end", iid=str(i),
                values=(s["name"], s["Task Duration"], s["break"], s["cycles"]),
                tags=(tag,)
            )
            self.tree.tag_configure(tag, background=colour)

    def sync_tree_to_sessions(self):
        self.sessions.clear()
        for iid in self.tree.get_children():
            name, work, brk, cyc = self.tree.item(iid, "values")
            self.sessions.append({
                "name": name,
                "Task Duration": int(work),
                "break": int(brk),
                "cycles": int(cyc)
            })
        self.save_sessions()

    def edit_cell(self, event):
        row = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row or col == "#0":
            return

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

    def selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    # ---------- TASK BUTTONS ----------

    def add_task(self):
        self.sessions.append({
            "name": "New Task",
            "Task Duration": 25,
            "break": 5,
            "cycles": 1
        })
        self.refresh_tree()
        self.save_sessions()

    def remove_task(self):
        idx = self.selected_index()
        if idx is None:
            return
        del self.sessions[idx]
        self.refresh_tree()
        self.save_sessions()

    # ---------- TIMER ----------

    def start_selected(self):
        idx = self.selected_index()
        if idx is None:
            return

        self.current_row = idx
        self.current_cycle = 1
        self.current_phase = "work"
        self.start_phase()

    def start_phase(self):
        task = self.sessions[self.current_row]

        if self.current_phase == "work":
            self.phase_total = task["Task Duration"] * 60
        else:
            self.phase_total = task["break"] * 60

        self.totalSeconds = self.phase_total
        self.progressValue.set(0)
        self.timerRunning = True
        self.paused = False

        self.update_time()
        self.play_music()  # Start music
        self.run_timer()

    def run_timer(self):
        if not self.timerRunning or self.paused:
            return

        if self.totalSeconds > 0:
            self.totalSeconds -= 1

            # Tracks time for 'work' phase
            if self.current_phase == "work":
                task_name = self.sessions[self.current_row]["name"]
                self.stats[task_name] = self.stats.get(task_name, 0) + 1

            self.update_time()

            progress = int(
                ((self.phase_total - self.totalSeconds) / self.phase_total) * 100
            )
            self.progressValue.set(progress)
            self.draw_progress_bar(progress)  # Update canvas bar

            self.currentJob = self.root.after(1000, self.run_timer)
        else:
            self.advance_phase()

    def advance_phase(self):
        task = self.sessions[self.current_row]
        self.stop_music()

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
        self.stop_music()

        if self.current_cycle < task["cycles"]:
            self.current_cycle += 1
            self.current_phase = "work"
            self.start_phase()
        else:
            self.timerRunning = False
            self.timeString.set("Task Done")
            self.root.after(15000, self.start_next_task)

    def start_next_task(self):
        next_row = self.current_row + 1
        if next_row < len(self.sessions):
            self.tree.selection_set(str(next_row))
            self.current_row = next_row
            self.current_cycle = 1
            self.current_phase = "work"
            self.start_phase()
        else:
            self.timeString.set("All tasks completed!")

    def pause_resume(self):
        if not self.timerRunning:
            return
        self.paused = not self.paused
        self.pauseBtn.config(text="Resume" if self.paused else "Pause")
        
        if self.paused:
            self.pause_music()
        else:
            self.unpause_music()
            self.run_timer()

    def stop_timer(self):
        self.timerRunning = False
        self.paused = False
        self.stop_music()
        self.progressValue.set(0)
        self.timeString.set("00:00")
        self.pauseBtn.config(text="Pause")
        self.draw_progress_bar(0)
        self.save_stats()

    def update_time(self):
        m, s = divmod(self.totalSeconds, 60)
        self.timeString.set(f"{m:02d}:{s:02d}")

    # ---------- PROGRESS BAR ----------

    def draw_progress_bar(self, percent):
        width = 320
        height = 20
        fill_width = int((percent / 100) * width)

        self.canvas.delete("all")

        theme = THEMES[self.current_theme]
        trough_color = theme["progress_trough"]
        fill_color = theme["progress_fill"]

        # Draw trough (background)
        self.canvas.create_rectangle(0, 0, width, height, fill=trough_color, outline="")

        # Draw beveled fill
        if fill_width > 0:
            # Main fill
            self.canvas.create_rectangle(0, 0, fill_width, height, fill=fill_color, outline="")

            # Top highlight line (bevel)
            self.canvas.create_line(0, 0, fill_width, 0, fill="white", width=1)

            # Left highlight line (bevel)
            self.canvas.create_line(0, 0, 0, height, fill="white", width=1)

    # ---------- THEMES ----------

    def switch_theme(self):
        order = ["light", "dark", "savana", "water"]
        self.current_theme = order[(order.index(self.current_theme) + 1) % len(order)]
        self.apply_ui_theme()
        self.refresh_tree()

    def apply_ui_theme(self):
        t = THEMES[self.current_theme]
        self.root.configure(bg=t["bg"])
        self.left.configure(bg=t["bg"])
        self.right.configure(bg=t["bg"])
        self.timerLabel.configure(bg=t["bg"], fg=t["fg"])
        self.canvas.configure(bg=t["progress_trough"])
        
        # Update all buttons in ctrl frame
        for btn in self.ctrl.winfo_children():
            if isinstance(btn, tk.Button):
                btn.configure(bg=t["button_bg"], fg=t["button_fg"])
        
        # Update buttons in btns frame
        for btn in self.btns.winfo_children():
            if isinstance(btn, tk.Button):
                btn.configure(bg=t["button_bg"], fg=t["button_fg"])
        
        # Update sound management buttons
        for btn in self.sound_btns.winfo_children():
            if isinstance(btn, tk.Button):
                btn.configure(bg=t["button_bg"], fg=t["button_fg"])
        
        # Update audio frame widgets
        self.audio_frame.configure(bg=t["bg"])
        self.vol_label.configure(bg=t["bg"], fg=t["fg"])
        
        # Redraw progress bar
        current_progress = self.progressValue.get()
        self.draw_progress_bar(current_progress)

    # ---------- SAVE ON EXIT ----------

    def on_closing(self):
        self.stop_music()
        self.save_sessions()
        self.save_stats()
        self.save_custom_sounds()
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

        for col, w in zip(
            ("Task Name", "Task Duration", "Break", "Cycles"),
            (160, 120, 80, 80)
        ):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        self.tree.column("Task Name", anchor="w")
        self.tree.pack()
        self.tree.bind("<Double-1>", self.edit_cell)

        # Task management buttons
        self.btns = tk.Frame(self.left)
        self.btns.pack(pady=6)

        tk.Button(self.btns, text="Add", width=6, command=self.add_task).grid(row=0, column=0, padx=3)
        tk.Button(self.btns, text="Remove", width=6, command=self.remove_task).grid(row=0, column=1, padx=3)
        tk.Button(self.btns, text="Save Now", width=8, command=self.save_sessions).grid(row=0, column=2, padx=3)

        # AUDIO CONTROLS
        tk.Label(self.left, text="Audio Settings", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        
        self.audio_frame = tk.Frame(self.left)
        self.audio_frame.pack(pady=5, fill=tk.X)
        
        self.vol_label = tk.Label(self.audio_frame, text="Volume")
        self.vol_label.pack(side=tk.LEFT, padx=5)
        
        self.volume_slider = tk.Scale(
            self.audio_frame, from_=0, to=100, orient="horizontal", 
            variable=self.volume_var, command=self.change_volume, showvalue=0
        )
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Sound selection dropdown
        sound_select_frame = tk.Frame(self.left)
        sound_select_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(sound_select_frame, text="Sound:").pack(side=tk.LEFT, padx=5)
        
        self.sound_var = tk.StringVar(value="Savana")
        self.sound_menu = tk.OptionMenu(
            sound_select_frame, self.sound_var, *sorted(self.sounds.keys()), 
            command=self.change_music_selection
        )
        self.sound_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Sound management buttons
        self.sound_btns = tk.Frame(self.left)
        self.sound_btns.pack(pady=6)
        
        tk.Button(self.sound_btns, text="+ Add Sound", width=12, 
                  command=self.add_custom_sound).grid(row=0, column=0, padx=3)
        tk.Button(self.sound_btns, text="− Remove Sound", width=12, 
                  command=self.remove_custom_sound).grid(row=0, column=1, padx=3)

        # RIGHT PANEL - Timer Display
        self.timerLabel = tk.Label(self.right, textvariable=self.timeString, font=("Arial", 32, "bold"))
        self.timerLabel.pack(pady=20)

        # Replace ttk.Progressbar with Canvas
        self.canvas = tk.Canvas(self.right, width=320, height=20, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(pady=10)

        self.ctrl = tk.Frame(self.right)
        self.ctrl.pack(pady=10)

        tk.Button(self.ctrl, text="Start", command=self.start_selected).grid(row=0, column=0, padx=5)
        self.pauseBtn = tk.Button(self.ctrl, text="Pause", command=self.pause_resume)
        self.pauseBtn.grid(row=0, column=1, padx=5)
        tk.Button(self.ctrl, text="Stop", command=self.stop_timer).grid(row=0, column=2, padx=5)
        tk.Button(self.ctrl, text="Switch Theme", command=self.switch_theme).grid(row=0, column=3, padx=5)


if __name__ == "__main__":
    root = tk.Tk()
    Pomodoro(root)
    root.mainloop()