import os
import json
import pandas as pd
import datetime
from fuzzywuzzy import fuzz, process

# --- HR Functions (shared) ---
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
    print(f"HR Matching: Target: {target_name}, Best Match: {best_match}")
    if best_match and best_match[1] >= threshold:
        hr_match = hr_df[hr_df["full_name"] == best_match[0]].iloc[0]
        return hr_match
    return None

# --- Telestaff Import ---
def convert_to_processed_format(vacation_dates, holiday_dates):
    processed_entries = []
    for date in vacation_dates:
        processed_entries.append({
            "date": date,
            "type": "Vacation",
            "determination": "Approved",
            "reason": None,
            "increments": "FULL",
            "place": None
        })
    for date in holiday_dates:
        processed_entries.append({
            "date": date,
            "type": "Holiday",
            "determination": "Approved",
            "reason": None,
            "increments": "FULL",
            "place": None
        })
    return processed_entries

def read_telestaff_export(excel_path, hr_excel_path="./HR_data_plus_ranks.xlsx"):
    try:
        hr_df = load_hr_data(hr_excel_path)
        print(f"Loaded HR data with {len(hr_df)} records from {hr_excel_path}")
    except Exception as e:
        print("Error loading HR data:", e)
        hr_df = None

    df_full = pd.read_excel(excel_path, header=None)
    date_range_str = str(df_full.iloc[2, 0]).strip()
    if date_range_str.startswith('[') and date_range_str.endswith(']'):
        date_range_str = date_range_str[1:-1].strip()
    if " - " in date_range_str:
        start_date_str, end_date_str = date_range_str.split(" - ")
    else:
        start_date_str, _, end_date_str = date_range_str.partition(" through ")
    start_date = pd.to_datetime(start_date_str.strip(), format='%m/%d/%Y')
    end_date = pd.to_datetime(end_date_str.strip(), format='%m/%d/%Y')

    data_header = df_full.iloc[4, :]
    raw_day_headers = data_header.iloc[4:].tolist()
    full_day_headers = []
    for dh in raw_day_headers:
        if isinstance(dh, (pd.Timestamp, datetime.datetime)):
            parsed = dh
        else:
            try:
                parsed = pd.to_datetime(str(dh).strip(), format='%m/%d', errors='coerce')
            except Exception as e:
                print(f"Error parsing date header {dh}: {e}")
                parsed = None
        if pd.isna(parsed) or parsed is None:
            full_day_headers.append(None)
        else:
            parsed = parsed.replace(year=start_date.year)
            if parsed < start_date:
                parsed = parsed.replace(year=start_date.year + 1)
            full_day_headers.append(parsed.strftime('%Y-%m-%d'))

    df_data = df_full.iloc[5:, :].copy()
    fixed_columns = ['Shift', 'Unused', 'Rank', 'Name']
    all_columns = fixed_columns + full_day_headers
    df_data = df_data.iloc[:, :len(all_columns)]
    df_data.columns = all_columns
    df_data['Shift'] = df_data['Shift'].ffill()
    df_data['Rank'] = df_data['Rank'].ffill()

    results = []
    for idx, row in df_data.iterrows():
        raw_shift = str(row['Shift']).strip()
        shift = raw_shift.split()[0]
        rank = row['Rank']
        name_field = row['Name']
        if pd.isna(name_field):
            continue
        name_str = str(name_field)
        parts = name_str.split(',')
        last_name = parts[0].strip() if parts else ""
        first_name = parts[1].split('(')[0].strip() if len(parts) > 1 else ""
        
        vacations = []
        holidays = []
        for col in full_day_headers:
            if col is None:
                continue
            cell = row[col]
            if isinstance(cell, str):
                code = cell.strip().upper()
                if code.startswith("*"):
                    continue
                if code in ["V", ".V"]:
                    vacations.append(col)
                elif code in ["H", ".H"]:
                    holidays.append(col)
        processed_data = convert_to_processed_format(vacations, holidays)
        
        emp_id = None
        hire_date = None
        years_of_service = None
        awarded_vacation_days = None
        awarded_holiday_days = None
        hr_rank = str(rank).strip()
        
        if hr_df is not None:
            hr_entry = match_hr_entry(first_name, last_name, hr_df)
            if hr_entry is not None:
                emp_id = hr_entry.get("Employee Number")
                if emp_id is not None:
                    emp_id = str(emp_id)
                hire_date = hr_entry.get("Hire Date")
                if pd.notna(hire_date):
                    try:
                        hire_date = pd.to_datetime(hire_date).strftime('%Y-%m-%d')
                    except Exception as e:
                        print("Error converting Hire Date:", e)
                        hire_date = str(hire_date)
                years_of_service = hr_entry.get("Years of Service")
                if years_of_service is not None:
                    years_of_service = str(years_of_service)
                
                vacation_leave_hours = hr_entry.get("# of Vacation Leave Hours awarded(as days)")
                holiday_leave_hours = hr_entry.get("# of Holiday Leave Hours awarded(as days)")
                try:
                    awarded_vacation_days = float(vacation_leave_hours) if vacation_leave_hours is not None else None
                except Exception as e:
                    awarded_vacation_days = None
                try:
                    awarded_holiday_days = float(holiday_leave_hours) if holiday_leave_hours is not None else None
                except Exception as e:
                    awarded_holiday_days = None
                
                hr_rank = hr_entry.get("Rank")
        
        firefighter_entry = {
            "idnum": emp_id,
            "fname": first_name.capitalize(),
            "lname": last_name.capitalize(),
            "name": f"{first_name}, {last_name[0]} (ID: '{emp_id}')",
            "rank": hr_rank,
            "shift": shift,
            "hireDate": str(hire_date) if pd.notna(hire_date) else None,
            "years_of_service": years_of_service,
            "awarded_vacation_days": awarded_vacation_days,
            "awarded_holiday_days": awarded_holiday_days,
            "max_days_off": (awarded_vacation_days + awarded_holiday_days) if awarded_vacation_days is not None and awarded_holiday_days is not None else None,
            "used_vacation_days": 0,
            "used_holiday_days": 0,
            "approved_days_count": 0,
            "picks": [],
            "processed": processed_data,
            "hr_validations": {},
            "exclusions": []
        }
        results.append(firefighter_entry)
    return results

# --- Supplemental Import (with HR matching) ---
def convert_to_pick_format_supp(day_date, selection_value):
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
    print("Supplemental Detected groups:", groups)
    
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
                # You may update awarded days similarly if desired.
        
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
            pick = convert_to_pick_format_supp(day_str, str(selection_val))
            if pick:
                firefighter_entry["picks"].append(pick)
        
        results.append(firefighter_entry)
    return results

# --- Merge Function ---
def merge_exports(telestaff_data, supplemental_data):
    """
    Merges telestaff and supplemental firefighter records.
    For each supplemental record, try to match based on shift, fname, and lname.
    If a match is found, extend its "picks" list with supplemental picks.
    Otherwise, add the supplemental record as new.
    """
    # Build lookup from telestaff data using key = (shift, fname, lname)
    lookup = {}
    for rec in telestaff_data:
        key = (rec.get("shift", "").strip().upper(),
               rec.get("fname", "").strip().upper(),
               rec.get("lname", "").strip().upper())
        lookup[key] = rec

    for s_rec in supplemental_data:
        key = (s_rec.get("shift", "").strip().upper(),
               s_rec.get("fname", "").strip().upper(),
               s_rec.get("lname", "").strip().upper())
        if key in lookup:
            # Merge supplemental picks into existing record.
            lookup[key]["picks"].extend(s_rec.get("picks", []))
        else:
            telestaff_data.append(s_rec)
    return telestaff_data

# --- Unified Processing and Output ---
def main():
    # Set file paths.
    telestaff_folder = "./telestaff_to_json/raw_telestaff_exports"
    supplemental_file = "./telestaff_to_json/supplemental_exports/2025 SUPPLEMENTAL VACATION REQUEST FORM - Form Responses.csv"
    hr_excel_path = "./HR_data_plus_ranks.xlsx"
    output_folder = "./telestaff_to_json/Output"
    os.makedirs(output_folder, exist_ok=True)

    # For telestaff, if you have separate files per shift, you can loop over them.
    shifts = ["A", "B", "C"]
    telestaff_data_all = []
    for shift in shifts:
        # Construct filename based on your naming convention.
        roster_date = "20250228"
        excel_filename = f"{roster_date} - Multiday Roster Report - {shift} Shift.xlsx"
        excel_file_path = os.path.join(telestaff_folder, excel_filename)
        print(f"Processing Telestaff file for shift {shift}: {excel_file_path}")
        try:
            data = read_telestaff_export(excel_file_path, hr_excel_path=hr_excel_path)
            print(f"Read {len(data)} records for shift {shift}.")
            telestaff_data_all.extend(data)
        except Exception as e:
            print(f"Error processing Telestaff file for shift {shift}: {e}")

    print(f"Total Telestaff records: {len(telestaff_data_all)}")
    
    # Read supplemental records.
    try:
        supplemental_data = read_supplemental_export(supplemental_file, hr_excel_path=hr_excel_path)
        print(f"Read {len(supplemental_data)} supplemental records.")
    except Exception as e:
        print(f"Error reading supplemental file: {e}")
        supplemental_data = []

    # Merge telestaff and supplemental data.
    unified_data = merge_exports(telestaff_data_all, supplemental_data)
    print(f"Unified record count after merging: {len(unified_data)}")

    # Write unified JSON file.
    output_filename = "Unified_FFighters.json"
    output_path = os.path.join(output_folder, output_filename)
    with open(output_path, "w") as f:
        json.dump(unified_data, f, indent=4)
    print(f"Unified JSON written to {output_path}")

if __name__ == "__main__":
    main()
