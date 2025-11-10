import pandas as pd
import datetime
from fuzzywuzzy import fuzz, process

# --- Existing functions (load_hr_data, match_hr_entry, convert_to_pick_format, read_supplemental_export) ---

def load_hr_data(hr_excel_path):
    hr_df = pd.read_excel(hr_excel_path)
    hr_df["Employee Name"] = hr_df["Employee Name"].astype(str)
    hr_df["Last Name"] = hr_df["Employee Name"].apply(lambda x: x.split(',')[0].strip().upper())
    hr_df["First Name"] = hr_df["Employee Name"].apply(
        lambda x: x.split(',')[1].split()[0].strip().upper() if ',' in x and len(x.split(',')) > 1 else ""
    )
    hr_df["full_name"] = hr_df["First Name"] + " " + hr_df["Last Name"]
    return hr_df

def match_hr_entry(first_name, last_name, hr_df, threshold=80):
    target_name = f"{first_name} {last_name}".upper()
    choices = hr_df["full_name"].tolist()
    best_match = process.extractOne(target_name, choices, scorer=fuzz.token_sort_ratio)
    print(f"Target: {target_name}, Best Match: {best_match}")  # Debug print
    if best_match and best_match[1] >= threshold:
        hr_match = hr_df[hr_df["full_name"] == best_match[0]].iloc[0]
        return hr_match
    return None

def convert_to_pick_format(day_date, selection_value):
    """
    For supplemental exports, create a pick using:
      - day_date from the Day column,
      - increments from the Shift Selection column.
    The pick is instantiated as:
      - type: "Untyped"
      - determination: "Unaddressed"
    """
    if not selection_value or selection_value.strip() == "":
        return None
    return {
        "date": day_date,
        "type": "Untyped",
        "source": "supplemental",
        "determination": "Unaddressed",
        "reason": None,
        "increments": selection_value.strip(),
        "place": None
    }

def read_supplemental_export(excel_path, hr_excel_path=None):
    """
    Reads a supplemental vacation selection export and converts it to a structured format.
    Optionally uses HR data (from hr_excel_path) to match and update firefighter details.
    
    Expected column order:
      - First 14 columns: basic firefighter info.
      - Columns 14 and onward: groups of three (Day, Shift Selection, Shift Check).
      - Final 5 columns: trailing fields to be ignored.
    """
    if excel_path.lower().endswith('.csv'):
        df = pd.read_csv(excel_path)
    else:
        df = pd.read_excel(excel_path)
    
    df.columns = [str(col).strip() for col in df.columns]
    
    fixed_columns = [
        "Submission Date", "First Name", "Last Name", "Email", 
        "Employee ID #", "Rank", "Shift", "Employee Hire Date", 
        "Acknowledgment of Form Completion", "Years of Service", 
        "Today", "Vacation Days Allowed", 
        "Probational Period:                   Holiday", 
        "Probational Period:                 Vacation"
    ]
    
    missing = [col for col in fixed_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")
    
    total_cols = list(df.columns)
    group_start = len(fixed_columns)
    trailing_count = 5
    group_end = len(total_cols) - trailing_count
    
    groups = []
    for i in range(group_start, group_end, 3):
        group = total_cols[i:i+3]
        if len(group) < 2:
            continue
        groups.append({
            "day_col": group[0],
            "selection_col": group[1]
        })
    print("Detected groups:", groups)
    
    hr_df = load_hr_data(hr_excel_path) if hr_excel_path else None
    
    results = []
    for idx, row in df.iterrows():
        first_name = str(row["First Name"]).strip()
        last_name = str(row["Last Name"]).strip()
        email = row["Email"]
        emp_id = row["Employee ID #"]
        rank = row["Rank"]
        shift = str(row["Shift"]).strip()
        hire_date = row["Employee Hire Date"]
        
        firefighter_entry = {
            "idnum": str(emp_id) if pd.notna(emp_id) else None,
            "fname": first_name.capitalize(),
            "lname": last_name.capitalize(),
            "name": f"{first_name}, {last_name[0] if last_name else ''} (ID: '{emp_id}')",
            "rank": rank,
            "shift": shift,
            "hireDate": pd.to_datetime(hire_date).strftime('%Y-%m-%d') if pd.notna(hire_date) else None,
            "years_of_service": row["Years of Service"],
            "email": email,
            "awarded_vacation_days": row["Vacation Days Allowed"],
            "max_days_off": None,
            "picks": [],
            "processed": [],
            "hr_validations": {},
            "exclusions": []
        }
        
        if hr_df is not None:
            hr_entry = match_hr_entry(first_name, last_name, hr_df)
            if hr_entry is not None:
                firefighter_entry["idnum"] = str(hr_entry.get("Employee Number", firefighter_entry["idnum"]))
                hr_hire_date = hr_entry.get("Hire Date")
                if pd.notna(hr_hire_date):
                    try:
                        firefighter_entry["hireDate"] = pd.to_datetime(hr_hire_date).strftime('%Y-%m-%d')
                    except Exception as e:
                        print("Error converting HR Hire Date:", e)
        
        for group in groups:
            day_val = row.get(group["day_col"])
            selection_val = row.get(group["selection_col"])
            if pd.isna(day_val) or pd.isna(selection_val):
                continue
            try:
                if isinstance(day_val, (datetime.datetime, pd.Timestamp)):
                    day_str = day_val.strftime('%Y-%m-%d')
                else:
                    day_str = pd.to_datetime(str(day_val)).strftime('%Y-%m-%d')
            except Exception:
                continue
            pick = convert_to_pick_format(day_str, str(selection_val))
            if pick:
                firefighter_entry["picks"].append(pick)
        
        results.append(firefighter_entry)
    
    return results

# --- New function: append_supplemental_picks ---

def match_supplemental_to_current(supp_record, current_data, threshold=80):
    """
    Attempt to match a supplemental record (with keys "fname", "lname", "shift") to a firefighter record
    in current_data. Uses exact name matching first, then fuzzy matching.
    Returns the matching record if found, else None.
    """
    target_fname = supp_record.get("fname", "").strip().upper()
    target_lname = supp_record.get("lname", "").strip().upper()
    target_shift = supp_record.get("shift", "").strip().upper()
    target_full = f"{target_fname} {target_lname}"
    
    candidates = [rec for rec in current_data if rec.get("shift", "").strip().upper() == target_shift]
    
    # Exact name match.
    for rec in candidates:
        if (rec.get("fname", "").strip().upper() == target_fname and 
            rec.get("lname", "").strip().upper() == target_lname):
            return rec
    
    # Fuzzy match if no exact match.
    best_match = None
    best_score = 0
    for rec in candidates:
        full_name_current = f"{rec.get('fname', '').strip().upper()} {rec.get('lname', '').strip().upper()}"
        score = fuzz.token_sort_ratio(target_full, full_name_current)
        if score > best_score:
            best_score = score
            best_match = rec
    if best_score >= threshold:
        return best_match
    return None

def append_supplemental_picks(current_data, supplemental_data):
    """
    Takes the current merged firefighter data and the supplemental records,
    and appends supplemental picks (from the "picks" key of each supplemental record)
    to the corresponding firefighter's "picks" list (if not already present).
    
    Returns updated current_data and a log list.
    """
    logs = []
    not_found = []  # Track supplemental records that could not be matched.
    appended_count = 0

    for supp_record in supplemental_data:
        # Attempt to match the supplemental record with current_data.
        match_rec = match_supplemental_to_current(supp_record, current_data)
        if not match_rec:
            not_found.append(f"{supp_record.get('fname','')} {supp_record.get('lname','')} (Shift: {supp_record.get('shift','')})")
            continue

        # For each supplemental pick, check if it's already in the "picks" list.
        for supp_pick in supp_record.get("picks", []):
            # Create a key tuple to compare: (date, type, determination, increments)
            supp_key = (supp_pick.get("date"), supp_pick.get("type"), supp_pick.get("determination"), supp_pick.get("increments"))
            exists = False
            for pick in match_rec.get("picks", []):
                pick_key = (pick.get("date"), pick.get("type"), pick.get("determination"), pick.get("increments"))
                if pick_key == supp_key:
                    exists = True
                    break
            if not exists:
                # Append supplemental pick to the "picks" list.
                match_rec.setdefault("picks", []).append(supp_pick)
                logs.append(f"Supplemental pick for {match_rec.get('fname','')} {match_rec.get('lname','')} on {supp_pick.get('date')} added.")
                appended_count += 1

    logs.append(f"\nSupplemental picks appended: {appended_count}.")
    if not_found:
        logs.append("No matching current record found for supplemental entries:")
        for entry in not_found:
            logs.append(" - " + entry)
    return current_data, logs


# --- Example usage ---
if __name__ == "__main__":
    import os
    excel_folder = "./telestaff_to_json/supplemental_exports"
    excel_filename = "2025 SUPPLEMENTAL VACATION REQUEST FORM - Form Responses.csv"
    excel_file_path = os.path.join(excel_folder, excel_filename)
    
    hr_excel_path = "./HR_data_plus_ranks.xlsx"
    
    # Read supplemental export.
    supplemental_data = read_supplemental_export(excel_file_path, hr_excel_path=hr_excel_path)
    
    # For demonstration, assume current_data is already merged from your compare_and_update process.
    # Here, we simulate by reading a merged JSON file.
    current_json_path = "./telestaff_to_json/Output/2025.03.04-FFighters_merged_ffighters.json"
    with open(current_json_path, 'r') as jf:
        current_data = pd.read_json(jf).to_dict(orient="records")  # or use json.load() if appropriate
    
    # Append supplemental picks.
    updated_data, supplemental_logs = append_supplemental_picks(current_data, supplemental_data)
    
    for log_entry in supplemental_logs:
        print(log_entry)
