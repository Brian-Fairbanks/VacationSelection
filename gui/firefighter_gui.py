# gui/firefighter_app.py
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
json_dir = "./output/Telestaff-Merged/"

class FirefighterApp:
    def __init__(self, root, logger):
        self.root = root
        self.logger = logger
        self.root.title("Firefighter Vacation Selection")
        self.root.geometry("1024x768")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Initialize filenames and data containers
        self.hr_filename = default_validation_filename
        self.pick_filename = default_picks_filename
        self.exclusions_filename = default_exclusions_filename
        self.ffighters = []
        self.shift_calendars = {}
        
        # Setup UI components
        self.create_file_selection_frame()
        self.create_action_buttons()
        self.setup_ffighter_tree_view()
        self.setup_pick_tree_view()

    def create_file_selection_frame(self):
        self.file_selection_frame = tk.Frame(self.root)
        self.file_selection_frame.pack(side=tk.TOP, pady=10, fill=tk.X)
        self.file_frame = tk.Frame(self.file_selection_frame)
        self.file_frame.pack(fill=tk.X)

        # HR File Selection
        self.hr_button = tk.Button(self.file_frame, text="Select HR Validation File", command=self.select_hr_file)
        self.hr_button.grid(row=0, column=0, padx=5, sticky='w')
        self.hr_label = tk.Label(self.file_frame, text=self.hr_filename, fg="black")
        self.hr_label.grid(row=0, column=1, padx=5, sticky='w')

        # Pick File Selection
        self.pick_button = tk.Button(self.file_frame, text="Select Firefighter Pick File", command=self.select_pick_file)
        self.pick_button.grid(row=1, column=0, padx=5, sticky='w')
        self.pick_label = tk.Label(self.file_frame, text=self.pick_filename, fg="black")
        self.pick_label.grid(row=1, column=1, padx=5, sticky='w')

        # Exclusions File Selection
        self.exclusions_button = tk.Button(self.file_frame, text="Select Exclusions File (Optional)", command=self.select_exclusions_file)
        self.exclusions_button.grid(row=2, column=0, padx=5, sticky='w')
        self.exclusions_label = tk.Label(self.file_frame, text=self.exclusions_filename, fg="black")
        self.exclusions_label.grid(row=2, column=1, padx=5, sticky='w')

        # Additional Buttons
        self.load_button = tk.Button(self.file_selection_frame, text="Load Firefighters", command=self.load_firefighters)
        self.load_button.pack(pady=10)
        self.read_json_button = tk.Button(self.file_selection_frame, text="Read From JSON", command=self.read_firefighters_from_json)
        self.read_json_button.pack(pady=10)
        self.make_calendar_button = tk.Button(self.file_selection_frame, text="Make Calendar", command=self.make_calendar)
        self.make_calendar_button.pack(pady=10)

    def create_action_buttons(self):
        self.validate_button = tk.Button(self.root, text="Validate Firefighters", command=self.validate_firefighters)
        self.validate_button.pack(pady=10)
        self.process_button = tk.Button(self.root, text="Process Selections", command=self.process_selections)
        self.process_button.pack(pady=10)

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

    def update_ffighters_tree(self, ffighters):
        update_treeview_data(self.ff_tree, [], clear_first=True)
        for ff in ffighters:
            num_picks = len(ff.picks)
            exclusions_display = format_exclusions(getattr(ff, "exclusions", []))
            # Prepare display values
            display_rank = self.get_display_value(ff, 'Rank')
            display_max_days_off = self.get_display_value(ff, 'Max Days Off')
            display_shift = self.get_display_value(ff, 'Shift')
            # Insert a row into the treeview
            self.ff_tree.insert('', 'end', values=(
                ff.idnum,
                ff.name,
                display_rank,
                display_max_days_off,
                display_shift,
                num_picks,
                exclusions_display
            ))

    def setup_ffighter_tree_view(self):
        self.ff_tree_frame = tk.Frame(self.root)
        self.ff_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ["ID", "Name", "Rank", "Max Days Off", "Shift", "Number of Picks", "Exclusions"]
        headings = columns
        widths = [50, 120, 80, 100, 50, 80, 200]
        self.ff_tree = create_treeview(self.ff_tree_frame, columns, headings, widths)
        self.ff_tree.bind('<<TreeviewSelect>>', self.on_ffighter_select)

    def setup_pick_tree_view(self):
        self.pick_tree_frame = tk.Frame(self.root)
        self.pick_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ["Date", "Type", "Determination", "Reason", "Increments"]
        headings = columns
        widths = [100, 80, 120, 150, 100]
        self.pick_tree = create_treeview(self.pick_tree_frame, columns, headings, widths)

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
                    pick.increments_plain_text()
                ))

    def get_display_value(self, ff, field_name):
        if ff.hr_validations and field_name in ff.hr_validations:
            previous_value, new_value = ff.hr_validations[field_name]
            return f"🔴 {new_value} (was {previous_value})"
        else:
            value = getattr(ff, field_name.replace(' ', '_').lower(), 'N/A')
            return f"⚪ {value}"

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
            messagebox.showwarning("No Calendar Found", "Please generate a calendar first.")
            return
        try:
            self.logger.info("Analyzing results and saving outputs.")
            all_ffighters = []
            for shift, calendar_data in self.shift_calendars.items():
                shift_ffighters = [ff for ff in self.ffighters if ff.shift == shift]
                all_ffighters.extend(shift_ffighters)
                write_ffighters_to_json(shift_ffighters, f'{shift}_ffighters', ".//output", datetime.now().strftime("%Y.%m.%d %H.%M"))
                write_calendar_to_csv(calendar_data["calendar"], shift, ".//output", datetime.now().strftime("%Y.%m.%d %H.%M"))
                write_picks_to_csv(shift_ffighters, shift, ".//output", datetime.now().strftime("%Y.%m.%d %H.%M"))
                print_final(shift_ffighters)
            analysis = analyze_results(all_ffighters)
            write_analysis_to_json(analysis, ".//output", datetime.now().strftime("%Y.%m.%d %H.%M"))
            display_dashboard(analysis)
            self.logger.info("Results analysis and saving complete.")
            messagebox.showinfo("Success", "Results analyzed and saved.")
        except Exception as e:
            self.logger.error(f"Error analyzing results: {e}")
            messagebox.showerror("Error", "Failed to analyze and save results.")

    def make_calendar(self):
        if not self.ffighters:
            messagebox.showwarning("No Firefighters Loaded", "Please load firefighter data before making a calendar.")
            return
        try:
            prioritized_ffighters = set_priorities(self.ffighters)
            for shift in ["A", "B", "C"]:
                shift_members = [ff for ff in prioritized_ffighters if ff.shift == shift]
                self.shift_calendars[shift] = make_calendar(shift_members)
            messagebox.showinfo("Success", "Calendar successfully created in memory.")
        except Exception as e:
            self.logger.error(f"Error creating calendar: {e}")
            messagebox.showerror("Error", "Failed to create calendar.")

    def make_calendar_from_json(self):
        if not self.ffighters:
            messagebox.showwarning("No Firefighters Loaded", "Please load firefighter data from JSON before making a calendar.")
            return
        try:
            self.shift_calendars = {}
            for shift in ["A", "B", "C"]:
                shift_members = [ff for ff in self.ffighters if ff.shift == shift]
                self.shift_calendars[shift] = recreate_calendar_from_json(shift_members)
            messagebox.showinfo("Success", "Calendar reconstructed from JSON and stored in memory.")
        except Exception as e:
            self.logger.error("Error reconstructing calendar", exc_info=True)
            messagebox.showerror("Error", "Failed to reconstruct calendar from JSON.")

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

        # so at this point firefighter_data has already been read in as a list of ffighter objects, right?
        if firefighter_data:
            # Run HR validation immediately after loading the JSON data.
            try:
                hr_data = read_hr_validation(self.hr_filename)  # so when it failes during this process right here, why would it be a dict?
            except Exception as e:
                self.logger.error(f"Failed to read HR file: {e}")
                messagebox.showerror("Error", "Failed to load HR data for validation.")
                return

            validated_ffighters = validate_against_hr(firefighter_data, hr_data)
            self.ffighters = validated_ffighters  # Update the internal list with validated entries

            # Recreate calendar using validated data.
            self.make_calendar_from_json()
            self.update_ffighters_tree(self.ffighters)
            messagebox.showinfo("Success", f"Loaded {len(validated_ffighters)} firefighters, validated them, and recreated calendar.")
        else:
            messagebox.showwarning("No Data", "No valid firefighter data was loaded.")

