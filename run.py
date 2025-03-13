# main.py
from datetime import datetime
import tkinter as tk
from vacation_selection.setup_logging import setup_logging
from gui.firefighter_gui import FirefighterApp

def main():
    runtime = datetime.now().strftime("%Y.%m.%d %H.%M")
    write_path = ".//output"
    logger = setup_logging(f"RunLog-{runtime}.log", base=write_path, debug=False)
    
    root = tk.Tk()
    app = FirefighterApp(root, logger)
    root.mainloop()

if __name__ == "__main__":
    main()
