import pandas as pd
import datetime
from fuzzywuzzy import fuzz, process

def load_hr_data(hr_excel_path):
    """
    Loads HR data from the given Excel file.
    Expected columns (adjust names as necessary):
      - Employee Number
      - Employee Name (formatted as "[Lastname, First Middle]")
      - Hire Date
      - Years of Service
      - # of Vacation Leave Hours awarded(as days)
      - # of Holiday Leave Hours awarded(as days)
      - Rank
    This function splits the "Employee Name" column into first and last names (ignoring middle names),
    then creates a 'full_name' column in the format "FIRST LAST" for matching.
    """
    hr_df = pd.read_excel(hr_excel_path)
    
    # Ensure the "Employee Name" column is string type.
    hr_df["Employee Name"] = hr_df["Employee Name"].astype(str)
    
    # Split "Employee Name" into Last Name and First Name (ignoring any middle names)
    hr_df["Last Name"] = hr_df["Employee Name"].apply(lambda x: x.split(',')[0].strip().upper())
    hr_df["First Name"] = hr_df["Employee Name"].apply(
        lambda x: x.split(',')[1].split()[0].strip().upper() if ',' in x and len(x.split(',')) > 1 else ""
    )
    
    # Create a full_name column for matching (first and last only, separated by a space)
    hr_df["full_name"] = hr_df["First Name"] + " " + hr_df["Last Name"]
    
    return hr_df



# --- New Function: Fuzzy Match HR Entry ---
def match_hr_entry(first_name, last_name, hr_df, threshold=80):
    target_name = f"{first_name} {last_name}".upper()
    choices = hr_df["full_name"].tolist()
    best_match = process.extractOne(target_name, choices, scorer=fuzz.token_sort_ratio)
    print(f"Target: {target_name}, Best Match: {best_match}")  # Debug print
    if best_match and best_match[1] >= threshold:
        hr_match = hr_df[hr_df["full_name"] == best_match[0]].iloc[0]
        return hr_match
    return None


def convert_to_processed_format(vacation_dates, holiday_dates):
    """
    Converts separate vacation and holiday date lists into the JSON 'processed' format.
    """
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
    """
    Reads a Telestaff export file and converts it into a structured JSON format.
    It also cross-references against HR data to fill in employee details.
    Returns a list of firefighter dictionaries.
    """
    # Load HR data first.
    try:
        hr_df = load_hr_data(hr_excel_path)
        print(f"Loaded HR data with {len(hr_df)} records from {hr_excel_path}")
    except Exception as e:
        print("Error loading HR data:", e)
        hr_df = None

    df_full = pd.read_excel(excel_path, header=None)

    # --- Extract the date range from row 3 (index 2) ---
    date_range_str = str(df_full.iloc[2, 0]).strip()
    if date_range_str.startswith('[') and date_range_str.endswith(']'):
        date_range_str = date_range_str[1:-1].strip()
    if " - " in date_range_str:
        start_date_str, end_date_str = date_range_str.split(" - ")
    else:
        start_date_str, _, end_date_str = date_range_str.partition(" through ")
    start_date = pd.to_datetime(start_date_str.strip(), format='%m/%d/%Y')
    end_date = pd.to_datetime(end_date_str.strip(), format='%m/%d/%Y')

    # --- Extract day headers from row 5 (index 4) for columns E onward ---
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

    # --- Data rows start from row 6 (index 5) ---
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
                # Skip pending requests
                if code.startswith("*"):
                    continue
                if code in ["V", ".V"]:
                    vacations.append(col)
                elif code in ["H", ".H"]:
                    holidays.append(col)
        processed_data = convert_to_processed_format(vacations, holidays)
        
        # Default HR info (if no match found, these remain None or the original)
        emp_id = None
        hire_date = None
        years_of_service = None
        vacation_leave_days = None
        holiday_leave_days = None
        awarded_vacation_days = None
        awarded_holiday_days = None
        hr_rank = str(rank).strip()  # fallback to Telestaff rank
        
        # Attempt to match against HR data if available.
        if hr_df is not None:
            hr_entry = match_hr_entry(first_name, last_name, hr_df)
            if hr_entry is not None:
                emp_id = hr_entry.get("Employee Number")
                if emp_id is not None:
                    emp_id = str(emp_id)
                hire_date = hr_entry.get("Hire Date")
                # Convert hire_date to date-only string if it is a datetime.
                if pd.notna(hire_date):
                    try:
                        hire_date = pd.to_datetime(hire_date).strftime('%Y-%m-%d')
                    except Exception as e:
                        print("Error converting Hire Date:", e)
                        hire_date = str(hire_date)
                years_of_service = hr_entry.get("Years of Service")
                if years_of_service is not None:
                    years_of_service = str(years_of_service)
                
                # Retrieve awarded leave values and cast to float if possible.
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
                
                # Optionally update rank based on HR.
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
            "awarded_vacation_days": awarded_vacation_days,  # HR awarded vacation days
            "awarded_holiday_days": awarded_holiday_days,      # HR awarded holiday days
            "max_days_off": (awarded_vacation_days + awarded_holiday_days)
                        if awarded_vacation_days is not None and awarded_holiday_days is not None else None,
            "used_vacation_days": 0,       # Initialize used days to zero; update based on processed picks
            "used_holiday_days": 0,        # Initialize used days to zero; update based on processed picks
            "approved_days_count": 0,      # Initialize approved days to zero
            "picks": [],
            "processed": processed_data,
            "hr_validations": {},        # For additional HR validation info if needed
            "exclusions": []
        }

        results.append(firefighter_entry)

    return results


# Example usage:
if __name__ == "__main__":
    import os
    # Define folder paths.
    json_folder = "./telestaff_to_json/2024_JSON_Place"
    excel_folder = "./telestaff_to_json/raw_telestaff_exports"
    output_folder = "./telestaff_to_json/Output"
    
    # Set the shift type and roster date for naming.
    shift_type = "C"  # Options: "A", "B", or "C"
    roster_date = "20250228"  # New naming convention date portion
    
    # Build Excel file path using the new naming convention.
    excel_filename = f"{roster_date} - Multiday Roster Report - {shift_type} Shift.xlsx"
    excel_file_path = os.path.join(excel_folder, excel_filename)

    data = read_telestaff_export(excel_file_path)
    for entry in data:
        print(entry)
