import os
import csv
import json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from difflib import SequenceMatcher

from vacation_selection.file_io import (
    read_firefighter_data, write_ffighters_to_json, write_calendar_to_csv,
    write_picks_to_csv, print_final, read_hr_validation, read_exclusions_file,
    write_analysis_to_json, read_ffighters_from_json
)
from vacation_selection.analyze import analyze_results, display_dashboard
from vacation_selection.main import validate_against_hr
from vacation_selection.priority import set_priorities
from vacation_selection.cal import make_calendar, recreate_calendar_from_json

# Import treeview helpers
from gui.tree_views import create_treeview, update_treeview_data, format_exclusions

# Default filenames/paths
default_picks_filename = "./2025 VACATION REQUEST FORM - Form Responses_final.csv"
default_validation_filename = "./HR_data_plus_ranks.xlsx"
default_exclusions_filename = "./exclusions.xlsx"
json_dir = "./output/telestaff+suplemental_merged/"

class FirefighterApp:
    def __init__(self, root, logger):
        self.root = root
        self.logger = logger
        self.root.title("Firefighter Vacation Selection")
        self.root.geometry("1024x768")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)
        
        # Initialize filenames and data containers
        self.hr_filename = default_validation_filename
        self.pick_filename = default_picks_filename
        self.exclusions_filename = default_exclusions_filename
        self.ffighters = []
        self.shift_calendars = {}

        # Set up the UI in separate frames
        self.setup_ui()

    def setup_ui(self):
        # ---------------------- Frame 1: Legacy Data Import ----------------------
        self.legacy_frame = tk.LabelFrame(self.root, text="Legacy Data Import (New Run)", padx=10, pady=10)
        self.legacy_frame.pack(fill="x", padx=10, pady=5)

        # HR File Selection
        self.hr_button = tk.Button(self.legacy_frame, text="Select HR Validation File", command=self.select_hr_file)
        self.hr_button.grid(row=0, column=0, padx=5, sticky='w')
        self.hr_label = tk.Label(self.legacy_frame, text=self.hr_filename, fg="black")
        self.hr_label.grid(row=0, column=1, padx=5, sticky='w')

        # Firefighter Pick File Selection
        self.pick_button = tk.Button(self.legacy_frame, text="Select Firefighter Pick File", command=self.select_pick_file)
        self.pick_button.grid(row=1, column=0, padx=5, sticky='w')
        self.pick_label = tk.Label(self.legacy_frame, text=self.pick_filename, fg="black")
        self.pick_label.grid(row=1, column=1, padx=5, sticky='w')

        # Exclusions File Selection (Optional)
        self.exclusions_button = tk.Button(self.legacy_frame, text="Select Exclusions File (Optional)", command=self.select_exclusions_file)
        self.exclusions_button.grid(row=2, column=0, padx=5, sticky='w')
        self.exclusions_label = tk.Label(self.legacy_frame, text=self.exclusions_filename, fg="black")
        self.exclusions_label.grid(row=2, column=1, padx=5, sticky='w')

        # Load Firefighters Button for Legacy Import
        self.load_button = tk.Button(self.legacy_frame, text="Load Firefighters", command=self.load_firefighters)
        self.load_button.grid(row=3, column=0, columnspan=2, pady=10)

        # ---------------------- Frame 2 & 3 Combined Horizontally ----------------------
        # Container frame for Expanded Data Import and Actions side-by-side
        self.horizontal_container = tk.Frame(self.root)
        self.horizontal_container.pack(fill="x", padx=10, pady=5)

        # Frame 2: Expanded Data Import
        self.expanded_frame = tk.LabelFrame(self.horizontal_container, text="Expand Existing Data (Load Previous Run JSON)", padx=10, pady=10)
        self.expanded_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        # Button to select folder and read JSON files
        self.read_json_button = tk.Button(self.expanded_frame, text="Read From JSON", command=self.read_firefighters_from_json)
        self.read_json_button.pack(pady=10, anchor='w')

        # Frame 3: Actions (now placed horizontally next to Expanded Data Import)
        self.action_frame = tk.LabelFrame(self.horizontal_container, text="Actions", padx=10, pady=10)
        self.action_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        # Validate Firefighters Button
        self.validate_button = tk.Button(self.action_frame, text="Validate Firefighters", command=self.validate_firefighters)
        self.validate_button.grid(row=0, column=0, padx=5, pady=5)
        # Generate Schedule Button (renamed from Make Calendar)
        self.generate_schedule_button = tk.Button(self.action_frame, text="Generate Schedule", command=self.make_calendar)
        self.generate_schedule_button.grid(row=0, column=1, padx=5, pady=5)
        # Finalize and Export Button (renamed from Process Selections)
        self.export_button = tk.Button(self.action_frame, text="Finalize and Export", command=self.process_selections)
        self.export_button.grid(row=0, column=2, padx=5, pady=5)

        # ---------------------- Frame 4: Data Display ----------------------
        self.data_frame = tk.LabelFrame(self.root, text="Data Display", padx=10, pady=10)
        self.data_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Firefighter Treeview Setup
        self.setup_ffighter_tree_view(self.data_frame)
        # Pick Treeview Setup
        self.setup_pick_tree_view(self.data_frame)

    # ---------------------- Legacy File Selection Functions ----------------------
    def select_hr_file(self):
        self.hr_filename = filedialog.askopenfilename(title="Select HR Validation File", filetypes=[("Excel files", "*.xlsx")])
        if self.hr_filename:
            self.logger.info(f"Selected HR Validation File: {self.hr_filename}")
            self.hr_label.config(text=self.hr_filename, fg="black")

    def select_pick_file(self):
        self.pick_filename = filedialog.askopenfilename(title="Select Firefighter Pick File", filetypes=[("CSV files", "*.csv")])
        if self.pick_filename:
            self.logger.info(f"Selected Firefighter Pick File: {self.pick_filename}")
            self.pick_label.config(text=self.pick_filename, fg="black")

    def select_exclusions_file(self):
        self.exclusions_filename = filedialog.askopenfilename(title="Select Exclusions File", filetypes=[("Excel files", "*.xlsx")])
        if self.exclusions_filename:
            self.logger.info(f"Selected Exclusions File: {self.exclusions_filename}")
            self.exclusions_label.config(text=self.exclusions_filename, fg="black")

    def load_firefighters(self):
        if not self.hr_filename or not self.pick_filename:
            messagebox.showwarning("Missing Files", "Please select both HR and Pick files.")
            return
        try:
            date_format = '%m-%d-%Y'
            self.ffighters = read_firefighter_data(self.pick_filename, date_format, 2025)
            if self.exclusions_filename:
                exclusions = read_exclusions_file(self.exclusions_filename)
                self.apply_exclusions(exclusions)
            self.update_ffighters_tree(self.ffighters)
        except Exception as e:
            self.logger.error(f"Error loading firefighter data: {e}")
            messagebox.showerror("Error", "Failed to load firefighter data.")

    def apply_exclusions(self, exclusions):
        unmatched_exclusions = []
        for exclusion in exclusions:
            lname_excl = exclusion['LName'].lower()
            fname_excl = exclusion['FName'].lower()
            leave_start = exclusion['Leave Start']
            leave_end = exclusion.get('Leave End')
            reason = exclusion['Reason']
            matched = False
            for ff in self.ffighters:
                lname_ff = ff.lname.lower()
                fname_ff = ff.fname.lower()
                last_name_match = SequenceMatcher(None, lname_excl, lname_ff).ratio() >= 0.8
                first_name_match = SequenceMatcher(None, fname_excl, fname_ff).ratio() >= 0.8
                swapped_names = fname_excl == lname_ff and lname_excl == fname_ff
                if (last_name_match and first_name_match) or swapped_names:
                    ff.add_exclusion(leave_start, leave_end, reason)
                    self.logger.info(f"Exclusion '{fname_excl} {lname_excl}' applied to '{ff.fname} {ff.lname}'.")
                    matched = True
                    break
            if not matched:
                unmatched_exclusions.append(f"{exclusion['FName']} {exclusion['LName']}")
        if unmatched_exclusions:
            unmatched_str = "\n".join(unmatched_exclusions)
            self.logger.warning(f"Unmatched exclusions:\n{unmatched_str}")
            messagebox.showwarning("Unmatched Exclusions",
                                   f"The following exclusions did not match any firefighter:\n{unmatched_str}")

    # ---------------------- Expanded Data Import Function ----------------------
    def read_firefighters_from_json(self):
        folder_selected = filedialog.askdirectory(initialdir=json_dir, title="Select Folder Containing JSON Files")
        if not folder_selected:
            return  # User canceled selection

        firefighter_data = []
        json_files = [f for f in os.listdir(folder_selected) if f.endswith('.json')]
        # Filter out analysis files
        json_files = [f for f in json_files if "analysis" not in f.lower()]

        if not json_files:
            messagebox.showwarning("No JSON Files", "No valid firefighter JSON files found in the selected folder.")
            return

        for json_file in json_files:
            file_path = os.path.join(folder_selected, json_file)
            try:
                ff_list = read_ffighters_from_json(file_path)
                firefighter_data.extend(ff_list)
                self.logger.info(f"Loaded {len(ff_list)} firefighters from {json_file}")
            except Exception as e:
                self.logger.error(f"Failed to read {json_file}: {e}")

        if firefighter_data:
            # Validate imported JSON data immediately using HR data
            try:
                hr_data = read_hr_validation(self.hr_filename)
            except Exception as e:
                self.logger.error(f"Failed to read HR file: {e}")
                messagebox.showerror("Error", "Failed to load HR data for validation.")
                return

            validated_ffighters = validate_against_hr(firefighter_data, hr_data)
            self.ffighters = validated_ffighters
            self.make_calendar_from_json()
            self.update_ffighters_tree(self.ffighters)
            messagebox.showinfo("Success", f"Loaded {len(validated_ffighters)} firefighters, validated them, and recreated calendar.")
        else:
            messagebox.showwarning("No Data", "No valid firefighter data was loaded.")

    def make_calendar_from_json(self):
        try:
            self.shift_calendars = {}
            for shift in ["A", "B", "C"]:
                shift_members = [ff for ff in self.ffighters if ff.shift == shift]
                self.shift_calendars[shift] = recreate_calendar_from_json(shift_members)
            messagebox.showinfo("Success", "Calendar reconstructed from JSON and stored in memory.")
        except Exception as e:
            self.logger.error(f"Error reconstructing calendar", exc_info=True)
            messagebox.showerror("Error", "Failed to reconstruct calendar from JSON.")

    # ---------------------- Common Actions ----------------------
    def validate_firefighters(self):
        if not self.ffighters:
            messagebox.showwarning("No Firefighters Loaded", "Please load firefighter data before validating.")
            return
        try:
            self.logger.debug(f"Reading HR validation data from file: {self.hr_filename}")
            hr_data = read_hr_validation(self.hr_filename)
            self.logger.debug(f"HR validation data loaded. Entries: {len(hr_data)}")
            validated_ffighters = validate_against_hr(self.ffighters, hr_data)
            self.ffighters = validated_ffighters
            self.update_ffighters_tree(validated_ffighters)
            verified_filename = f"{self.pick_filename.split('.')[0]}-Verified.csv"
            self.logger.debug(f"Writing validated data to: {verified_filename}")
            with open(verified_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["ID", "Name", "Hire Date", "Rank", "Shift", "Max Days Off", "Approved Days Count"])
                for ff in validated_ffighters:
                    writer.writerow([ff.idnum, ff.name, ff.hireDate, ff.rank, ff.shift, ff.max_days_off, ff.approved_days_count])
            self.logger.info(f"Validated data written to {verified_filename}")
        except Exception as e:
            self.logger.error(f"Error validating firefighter data: {e}")
            messagebox.showerror("Error", "Failed to validate firefighter data.")

    def process_selections(self):
        if not self.shift_calendars:
            messagebox.showwarning("No Calendar Found", "Please generate a schedule first.")
            return
        try:
            self.logger.info("Analyzing results and saving outputs.")
            all_ffighters = []
            runtime_str = datetime.now().strftime("%Y.%m.%d %H.%M")
            for shift, calendar_data in self.shift_calendars.items():
                shift_ffighters = [ff for ff in self.ffighters if ff.shift == shift]
                all_ffighters.extend(shift_ffighters)
                write_ffighters_to_json(shift_ffighters, f'{shift}_ffighters', ".//output", runtime_str)
                write_calendar_to_csv(calendar_data["calendar"], shift, ".//output", runtime_str)
                write_picks_to_csv(shift_ffighters, shift, ".//output", runtime_str)
                # Write supplemental-only picks using a filter function:
                write_picks_to_csv(shift_ffighters, f'{shift}_supplemental', ".//output", runtime_str,
                                pick_filter=lambda pick: pick.source and pick.source.lower() == "supplemental")
                print_final(shift_ffighters)
            analysis = analyze_results(all_ffighters)
            write_analysis_to_json(analysis, ".//output", runtime_str)
            display_dashboard(analysis)
            self.logger.info("Results analysis and saving complete.")
            messagebox.showinfo("Success", "Results analyzed and saved.")
        except Exception as e:
            self.logger.exception("Error analyzing results")
            messagebox.showerror("Error", "Failed to analyze and save results.")


    def make_calendar(self):
        if not self.ffighters:
            messagebox.showwarning("No Firefighters Loaded", "Please load firefighter data before generating a schedule.")
            return
        try:
            prioritized_ffighters = set_priorities(self.ffighters)
            for shift in ["A", "B", "C"]:
                if not self.shift_calendars[shift]:self.shift_calendars[shift]={}
                shift_members = [ff for ff in prioritized_ffighters if ff.shift == shift]
                self.shift_calendars[shift] = make_calendar(shift_members, existing_calendar_data=self.shift_calendars[shift], count=1)
            messagebox.showinfo("Success", "Schedule successfully generated and stored in memory.")
        except Exception as e:
            self.logger.error(f"Error generating schedule: {e}")
            messagebox.showerror("Error", "Failed to generate schedule.")

    # ---------------------- Data Display ----------------------
    def setup_ffighter_tree_view(self, parent):
        self.ff_tree_frame = tk.Frame(parent)
        self.ff_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ["ID", "Name", "Rank", "Max Days Off", "Shift", "Number of Picks", "Exclusions"]
        headings = columns
        widths = [50, 120, 80, 100, 50, 80, 200]
        self.ff_tree = create_treeview(self.ff_tree_frame, columns, headings, widths)
        self.ff_tree.bind('<<TreeviewSelect>>', self.on_ffighter_select)

    def setup_pick_tree_view(self, parent):
        self.pick_tree_frame = tk.Frame(parent)
        self.pick_tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        # Added "Source" column
        columns = ["Date", "Type", "Determination", "Reason", "Increments", "Source"]
        headings = columns
        widths = [100, 80, 120, 150, 100, 150]  # Adjust widths as needed
        self.pick_tree = create_treeview(self.pick_tree_frame, columns, headings, widths)

    def update_ffighters_tree(self, ffighters):
        update_treeview_data(self.ff_tree, [], clear_first=True)
        for ff in ffighters:
            num_picks = len(ff.picks)
            exclusions_display = format_exclusions(getattr(ff, "exclusions", []))
            display_rank = self.get_display_value(ff, 'Rank')
            display_max_days_off = self.get_display_value(ff, 'Max Days Off')
            display_shift = self.get_display_value(ff, 'Shift')
            self.ff_tree.insert('', 'end', values=(
                ff.idnum,
                ff.name,
                display_rank,
                display_max_days_off,
                display_shift,
                num_picks,
                exclusions_display
            ))

    def on_ffighter_select(self, event):
        selected_item = self.ff_tree.selection()
        if selected_item:
            ff_id = self.ff_tree.item(selected_item)['values'][0]
            ff = next((f for f in self.ffighters if str(f.idnum) == str(ff_id)), None)
            if ff:
                self.update_pick_tree(ff)

    def update_pick_tree(self, ff):
        update_treeview_data(self.pick_tree, [], clear_first=True)
        if hasattr(ff, 'processed') and hasattr(ff, 'picks'):
            for pick in ff.processed + ff.picks:
                if pick.determination == "Unaddressed":
                    determination_display = "⚪ Unprocessed"
                elif pick.determination == "Approved":
                    determination_display = "🟢 Approved"
                elif pick.determination == "Rejected":
                    determination_display = "🔴 Rejected"
                else:
                    determination_display = pick.determination
                self.pick_tree.insert('', 'end', values=(
                    pick.date,
                    pick.type,
                    determination_display,
                    pick.reason if pick.reason else "N/A",
                    pick.increments_plain_text(),
                    pick.source
                ))

    def get_display_value(self, ff, field_name):
        if ff.hr_validations and field_name in ff.hr_validations:
            previous_value, new_value = ff.hr_validations[field_name]
            return f"🔴 {new_value} (was {previous_value})"
        else:
            value = getattr(ff, field_name.replace(' ', '_').lower(), 'N/A')
            return f"⚪ {value}"

if __name__ == '__main__':
    import logging
    from vacation_selection.setup_logging import setup_logging
    # Set up logging
    runtime = datetime.now().strftime("%Y.%m.%d %H.%M")
    write_path = ".//output"
    logger = setup_logging(f"RunLog-{runtime}.log", base=write_path, debug=False)

    root = tk.Tk()
    app = FirefighterApp(root, logger)
    root.mainloop()
