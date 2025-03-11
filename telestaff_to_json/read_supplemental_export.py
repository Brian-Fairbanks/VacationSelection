import pandas as pd
import datetime

def convert_to_pick_format(day_date, code):
    """
    Converts a day/date and a pick code (e.g., 'V' or 'H') into a pick object.
    This pick is unprocessed and will go into the "picks" field.
    """
    pick_type = None
    if code.upper() in ["V", ".V"]:
        pick_type = "Vacation"
    elif code.upper() in ["H", ".H"]:
        pick_type = "Holiday"
    else:
        return None  # unrecognized code; skip it

    return {
        "date": day_date,
        "type": pick_type,
        "source": "supplemental",  # mark the origin
        "determination": "Pending",  # will be processed later
        "reason": None,
        "increments": "FULL",
        "place": None
    }

def read_supplemental_export(excel_path):
    """
    Reads a supplemental vacation selection export and converts it to a structured format.
    
    Expected column order (as provided):
      0: Submission Date
      1: First Name
      2: Last Name
      3: Email
      4: Employee ID #
      5: Rank
      6: Shift
      7: Employee Hire Date
      8: Acknowledgment of Form Completion
      9: Years of Service
      10: Today
      11: Vacation Days Allowed
      12: Probational Period: Holiday
      13: Probational Period: Vacation
      14 and onward: Repeating groups of three columns:
           - Day X, Shift Selection X, Shift Check X
           
    We will use only the basic identifying columns and process the groups to extract picks.
    """
    df = pd.read_excel(excel_path)

    # Define fixed columns that we want to keep.
    fixed_columns = [
        "Submission Date", "First Name", "Last Name", "Email", 
        "Employee ID #", "Rank", "Shift", "Employee Hire Date", 
        "Acknowledgment of Form Completion", "Years of Service", 
        "Today", "Vacation Days Allowed", "Probational Period: Holiday", 
        "Probational Period: Vacation"
    ]

    # Ensure we have the expected fixed columns.
    missing = [col for col in fixed_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # The rest of the columns are in groups of three: Day, Shift Selection, Shift Check.
    # We assume these start at index 14.
    total_cols = list(df.columns)
    group_start = len(fixed_columns)
    groups = []
    # Make groups of three for all remaining columns.
    for i in range(group_start, len(total_cols), 3):
        group = total_cols[i:i+3]
        if len(group) < 2:
            continue  # skip incomplete groups
        groups.append({
            "day_col": group[0],
            "selection_col": group[1]
            # We ignore the "Shift Check" column (group[2]) for now.
        })

    results = []
    # Process each row.
    for idx, row in df.iterrows():
        first_name = str(row["First Name"]).strip()
        last_name = str(row["Last Name"]).strip()
        email = row["Email"]
        emp_id = row["Employee ID #"]
        rank = row["Rank"]
        shift = str(row["Shift"]).strip()
        hire_date = row["Employee Hire Date"]

        # Start building the firefighter entry.
        firefighter_entry = {
            "idnum": str(emp_id) if pd.notna(emp_id) else None,
            "fname": first_name.capitalize(),
            "lname": last_name.capitalize(),
            "name": f"{first_name}, {last_name[0] if last_name else ''} (ID: '{emp_id}')",
            "rank": rank,
            "shift": shift,
            "hireDate": pd.to_datetime(hire_date).strftime('%Y-%m-%d') if pd.notna(hire_date) else None,
            "years_of_service": row["Years of Service"],
            # For HR/leave data we can store other fields if needed:
            "email": email,
            "awarded_vacation_days": row["Vacation Days Allowed"],
            # We'll compute max_days_off later as needed.
            "max_days_off": None,
            # For picks: supplemental picks will be stored here.
            "picks": [],
            # We'll keep the "processed" field empty for supplemental records.
            "processed": [],
            "hr_validations": {},
            "exclusions": []
        }

        # Process each group to extract picks.
        for group in groups:
            day_val = row.get(group["day_col"])
            selection_val = row.get(group["selection_col"])
            if pd.isna(day_val) or pd.isna(selection_val):
                continue
            # Assume day_val holds a date. Try to parse it.
            try:
                # If it's already a datetime, format it.
                if isinstance(day_val, (datetime.datetime, pd.Timestamp)):
                    day_str = day_val.strftime('%Y-%m-%d')
                else:
                    # Otherwise, try parsing.
                    day_str = pd.to_datetime(str(day_val)).strftime('%Y-%m-%d')
            except Exception as e:
                continue  # skip if the day cannot be parsed

            code = str(selection_val).strip()
            # Skip if the code indicates an unconfirmed or error state (if needed).
            pick = convert_to_pick_format(day_str, code)
            if pick:
                firefighter_entry["picks"].append(pick)

        results.append(firefighter_entry)

    return results

# Example usage:
if __name__ == "__main__":
    import os
    # Set file paths as needed.
    excel_folder = "./supplemental_exports"
    excel_filename = "supplemental_vacation_selection.xlsx"
    excel_file_path = os.path.join(excel_folder, excel_filename)

    data = read_supplemental_export(excel_file_path)
    for entry in data:
        print(entry)
