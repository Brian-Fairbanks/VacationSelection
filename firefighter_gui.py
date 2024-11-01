import tkinter as tk
from tkinter import filedialog, messagebox
import csv
from datetime import datetime
from vacation_selection.setup_logging import setup_logging
from vacation_selection.file_io import read_firefighter_data, write_ffighters_to_json, write_calendar_to_csv, write_picks_to_csv, print_final, read_hr_validation
from vacation_selection.main import validate_against_hr
from vacation_selection.priority import set_priorities
from vacation_selection.cal import make_calendar

# Set up runtime and logging
runtime = datetime.now().strftime("%Y.%m.%d %H.%M")
write_path = ".//output"
logger = setup_logging(f"RunLog-{runtime}.log", base=write_path, debug=False)

class FirefighterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firefighter Vacation Selection")
        
        self.hr_filename = ""
        self.pick_filename = ""
        self.ffighters = []

        # UI Elements
        self.hr_button = tk.Button(root, text="Select HR Validation File", command=self.select_hr_file)
        self.hr_button.pack(pady=10)

        self.hr_label = tk.Label(root, text="No HR file selected", fg="grey")
        self.hr_label.pack(pady=5)

        self.pick_button = tk.Button(root, text="Select Firefighter Pick File", command=self.select_pick_file)
        self.pick_button.pack(pady=10)

        self.pick_label = tk.Label(root, text="No Pick file selected", fg="grey")
        self.pick_label.pack(pady=5)

        self.load_button = tk.Button(root, text="Load Firefighters", command=self.load_firefighters)
        self.load_button.pack(pady=10)

        self.validate_button = tk.Button(root, text="Validate Firefighters", command=self.validate_firefighters)
        self.validate_button.pack(pady=10)

        self.process_button = tk.Button(root, text="Process Selections", command=self.process_selections)
        self.process_button.pack(pady=10)

        self.text_area = tk.Text(root, height=20, width=100)
        self.text_area.pack(pady=10)

    def select_hr_file(self):
        self.hr_filename = filedialog.askopenfilename(title="Select HR Validation File", filetypes=[("Excel files", "*.xlsx")])
        if self.hr_filename:
            logger.info(f"Selected HR Validation File: {self.hr_filename}")
            self.hr_label.config(text=self.hr_filename, fg="black")

    def select_pick_file(self):
        self.pick_filename = filedialog.askopenfilename(title="Select Firefighter Pick File", filetypes=[("CSV files", "*.csv")])
        if self.pick_filename:
            logger.info(f"Selected Firefighter Pick File: {self.pick_filename}")
            self.pick_label.config(text=self.pick_filename, fg="black")

    def load_firefighters(self):
        if not self.hr_filename or not self.pick_filename:
            messagebox.showwarning("Missing Files", "Please select both HR and Pick files.")
            return
        
        try:
            date_format = '%m-%d-%Y'
            self.ffighters = read_firefighter_data(self.pick_filename, date_format, 2025)
            self.display_firefighters(self.ffighters)
        except Exception as e:
            logger.error(f"Error loading firefighter data: {e}")
            messagebox.showerror("Error", "Failed to load firefighter data.")

    def display_firefighters(self, ffighters):
        self.text_area.delete(1.0, tk.END)
        for ff in ffighters:
            self.text_area.insert(tk.END, f"{ff}\n")

    def validate_firefighters(self):
        if not self.ffighters:
            messagebox.showwarning("No Firefighters Loaded", "Please load firefighter data before validating.")
            return

        try:
            hr_data = read_hr_validation(self.hr_filename)
            validated_ffighters = validate_against_hr(self.ffighters, hr_data)
            self.display_firefighters(validated_ffighters)
            
            # Write validated data to CSV
            verified_filename = f"{self.pick_filename.split('.')[0]}-Verified.csv"
            with open(verified_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["ID", "Name", "Hire Date", "Rank", "Shift", "Max Days Off", "Approved Days Count"])
                for ff in validated_ffighters:
                    writer.writerow([ff.idnum, ff.name, ff.hireDate, ff.rank, ff.shift, ff.max_days_off, ff.approved_days_count])
            
            logger.info(f"Validated firefighter data written to {verified_filename}")
        except Exception as e:
            logger.error(f"Error validating firefighter data: {e}")
            messagebox.showerror("Error", "Failed to validate firefighter data.")

    def process_selections(self):
        if not self.ffighters:
            messagebox.showwarning("No Firefighters Loaded", "Please load firefighter data before processing.")
            return
        
        try:
            # Set priorities for firefighters
            prioritized_ffighters = set_priorities(self.ffighters)

            # Process selections for each shift
            for shift in ["A", "B", "C"]:
                shift_members = [ff for ff in prioritized_ffighters if ff.shift == shift]
                results = make_calendar(shift_members)

                # Write outputs
                write_ffighters_to_json(shift_members, f'{shift}_ffighters', write_path, runtime)
                write_calendar_to_csv(results['calendar'], shift, write_path, runtime)
                write_picks_to_csv(shift_members, shift, write_path, runtime)
                print_final(shift_members)

            logger.info("Processing complete.")
            messagebox.showinfo("Success", "Processing complete.")
        except Exception as e:
            logger.error(f"Error processing selections: {e}")
            messagebox.showerror("Error", "Failed to process selections.")

if __name__ == '__main__':
    root = tk.Tk()
    app = FirefighterApp(root)
    root.mainloop()
