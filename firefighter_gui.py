import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
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
        self.root.geometry("1024x768")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        self.hr_filename = ""
        self.pick_filename = ""
        self.ffighters = []

        # UI Elements
        # ---------------------- File Selection Frame ----------------------
        self.file_selection_frame = tk.Frame(root)
        self.file_selection_frame.pack(side=tk.TOP, pady=10, fill=tk.X)
        self.file_frame = tk.Frame(self.file_selection_frame)
        self.file_frame.pack(fill=tk.X)

        # HR File Selection
        self.hr_button = tk.Button(self.file_frame, text="Select HR Validation File", command=self.select_hr_file)
        self.hr_button.grid(row=0, column=0, padx=5)
        self.hr_label = tk.Label(self.file_frame, text="No HR file selected", fg="grey")
        self.hr_label.grid(row=0, column=1, padx=5)

        # Pick File Selection
        self.pick_button = tk.Button(self.file_frame, text="Select Firefighter Pick File", command=self.select_pick_file)
        self.pick_button.grid(row=1, column=0, padx=5)
        self.pick_label = tk.Label(self.file_frame, text="No Pick file selected", fg="grey")
        self.pick_label.grid(row=1, column=1, padx=5)

        # Load Firefighters Button
        self.load_button = tk.Button(self.file_frame, text="Load Firefighters", command=self.load_firefighters)
        self.load_button.grid(row=2, column=0, columnspan=2, pady=5)

        # ---------------------- End of File Selection Frame ----------------------
        
        # Validation and Processing Elements
        self.validate_button = tk.Button(root, text="Validate Firefighters", command=self.validate_firefighters)
        self.validate_button.pack(pady=10)

        self.process_button = tk.Button(root, text="Process Selections", command=self.process_selections)
        self.process_button.pack(pady=10)

        self.setup_ffighter_tree_view()

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
            self.update_ffighters_tree(self.ffighters)
        except Exception as e:
            logger.error(f"Error loading firefighter data: {e}")
            messagebox.showerror("Error", "Failed to load firefighter data.")

    def update_ffighters_tree(self, ffighters):
        # Clear previous entries
        for item in self.ff_tree.get_children():
            self.ff_tree.delete(item)
        
        # Add firefighters to the Treeview
        for ff in ffighters:
            self.display_ffighter(ff)

    def setup_ffighter_tree_view(self):
        # Treeview for displaying firefighters
        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.ff_tree = ttk.Treeview(self.tree_frame, columns=("ID", "Name", "Rank", "Years of Service", "Shift", "Number of Picks", "Type", "Determination", "Reason", "Increments"), show='tree headings', selectmode='browse')
        self.ff_tree.heading("#0", text="Firefighter", anchor='w')
        self.ff_tree.heading("ID", text="ID", anchor='w')
        self.ff_tree.heading("Name", text="Name", anchor='w')
        self.ff_tree.heading("Rank", text="Rank", anchor='w')
        self.ff_tree.heading("Years of Service", text="Years of Service", anchor='w')
        self.ff_tree.heading("Shift", text="Shift", anchor='w')
        self.ff_tree.heading("Number of Picks", text="Number of Picks", anchor='w')
        self.ff_tree.heading("Type", text="Type", anchor='w')
        self.ff_tree.heading("Determination", text="Determination", anchor='w')
        self.ff_tree.heading("Reason", text="Reason", anchor='w')
        self.ff_tree.heading("Increments", text="Increments", anchor='w')

        # Set column widths for better readability
        self.ff_tree.column("ID", width=50, anchor='w')
        self.ff_tree.column("Name", width=120, anchor='w')
        self.ff_tree.column("Rank", width=80, anchor='w')
        self.ff_tree.column("Years of Service", width=100, anchor='w')
        self.ff_tree.column("Shift", width=50, anchor='w')
        self.ff_tree.column("Number of Picks", width=80, anchor='w')
        self.ff_tree.column("Type", width=80, anchor='w')
        self.ff_tree.column("Determination", width=100, anchor='w')
        self.ff_tree.column("Reason", width=120, anchor='w')
        self.ff_tree.column("Increments", width=80, anchor='w')
        self.ff_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def display_ffighter(self, ff):
        years_of_service = (datetime.now().date() - ff.hireDate).days // 365
        num_picks = len(ff.picks)
        parent = self.ff_tree.insert('', 'end', text=ff.name, values=(ff.idnum, ff.name, ff.rank, years_of_service, ff.shift, num_picks))
        
        # Add Picks directly under the firefighter, indicating processed or unprocessed
        for pick in ff.processed + ff.picks:
            status = "Processed" if pick in ff.processed else "Unprocessed"
            self.ff_tree.insert(parent, 'end', text=f"{status}", values=('','','','','',pick.date,pick.type, pick.determination, pick.reason if pick.reason else "N/A", pick.increments_plain_text()))

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
