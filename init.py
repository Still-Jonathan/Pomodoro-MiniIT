import tkinter as tk

class Pomodoro:
    def __init__(self, root):
        self.root = root

    def main(self):
        # Timer display
        self.min = tk.StringVar(self.root)
        self.min.set("25")
        self.sec = tk.StringVar(self.root)
        self.sec.set("00")

        # Minutes & Seconds font
        self.minLabel = tk.Label(self.root,
								textvariable=self.min, 
                                font=("arial", 22, "bold"), 
                                fg='black')
        self.minLabel.pack()

        self.secLabel = tk.Label(self.root,
								textvariable=self.sec, 
                                font=("arial", 18, "bold"), 
                                fg='black')
        self.secLabel.pack()

        self.root.mainloop()

if __name__ == '__main__':
	pomo = Pomodoro(tk.Tk())
	pomo.main()
