import tkinter as tk
import time
import json
import os

class Pomodoro:
    def __init__(self, root, configFile='config.json'):
        self.root = root
        self.configData = self.LoadConfig(configFile)

        # Timer states
        self.totalSeconds = 10 # 25 * 60 # The default 25 minutes
        self.timerRunning = False
        self.currentJob = None

    def LoadConfig(self, configFile):
        if not os.path.exists(configFile):
              print(f"Err: Config file '{configFile}' missing.")
              # Default font
              return {
                "timer_font": {
                    "family": "arial",
                    "size_min": 25,
                    "style_min": "bold",
                    "size_sec": 20,
                    "style_sec": "bold"
                },
                "colors": {
                    "text_fg": "black"
                }
            }
         
        with open(configFile, 'r') as f:
              return json.load(f)

    def main(self):
        # Load font config
        fontConfig = self.configData.get("timer_font", {})
        colourConfig = self.configData.get("colours", {})

        # Timer display
        self.timeString = tk.StringVar(self.root)
        self.timeString.set(f"{self.totalSeconds // 60:02d}:{self.totalSeconds % 60:02d}")

        timerFont = (
            fontConfig.get("family", "arial"), 
            fontConfig.get("size_min", 22), 
            fontConfig.get("style_min", "bold")
        )
        textColour = colourConfig.get("text_fg", "black")

        # Minutes & Seconds font
        self.timerLabel = tk.Label(self.root,
                                 textvariable=self.timeString, 
                                 font=timerFont, # <-- Uses the loaded font data
                                 fg=textColour) # <-- Uses the loaded color data
        self.timerLabel.pack()

        # Button
        self.startButton = tk.Button(self.root,
                                     text="Start",
                                     command=self.StartTimer,
                                     font=("arial", 12))
        self.startButton.pack(pady=10)

        self.root.mainloop()

    def StartTimer(self):
        if not self.timerRunning:
            self.timerRunning = True
            self.startButton.config(text="In Progress", state=tk.DISABLED)
            self.Countdown()

    def Countdown(self):
        if self.totalSeconds > 0:
            self.totalSeconds -= 1
        
            minutes = self.totalSeconds // 60
            seconds = self.totalSeconds % 60

            newTimeDisplay = f"{minutes:02d}:{seconds:02d}"

            self.timeString.set(newTimeDisplay)

            self.currentJob = self.root.after(1000, self.Countdown)
        
        else:
            self.timerRunning = False
            self.timeString.set("Finished")
            self.startButton.config(text="Start", state=tk.NORMAL)

if __name__ == '__main__':
    rootWindow = tk.Tk()
    rootWindow.title("Pomodoro App")

    pomo = Pomodoro(rootWindow)
    pomo.main()
