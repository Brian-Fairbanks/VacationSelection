# read_telestaff_export.py
import pandas as pd
import datetime


def convert_to_processed_format(vacation_dates, holiday_dates):
    """
    Converts separate vacation and holiday date lists into the JSON 'processed' format.

    Parameters:
        vacation_dates (list): List of vacation dates (YYYY-MM-DD).
        holiday_dates (list): List of holiday dates (YYYY-MM-DD).

    Returns:
        list: A list of dictionaries in "processed" format.
    """
    processed_entries = []

    # Convert vacations
    for date in vacation_dates:
        processed_entries.append({
            "date": date,
            "type": "Vacation",
            "determination": "Approved",
            "reason": None,  # No reason needed since everything is approved
            "increments": "FULL",  # Defaulting to FULL for now
            "place": None  # Default to None; can be handled later when needed
        })

    # Convert holidays
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


def read_telestaff_export(excel_path):
    """
    Reads a Telestaff export file and converts it into a structured format matching JSON output.

    Returns:
        list of dictionaries, each representing a firefighter.
    """
    df_full = pd.read_excel(excel_path, header=None)

    # --- Extract the date range from row 3 (index 2) ---
    date_range_str = df_full.iloc[2, 0]
    date_range_str = str(date_range_str).strip()
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
        if isinstance(dh, pd.Timestamp) or isinstance(dh, datetime.datetime):
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
        # Extract and clean up shift name
        raw_shift = str(row['Shift']).strip()
        shift = raw_shift.split()[0]  # Keep only "A", "B", or "C"

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
                if code == "V":
                    vacations.append(col)
                elif code == "H":
                    holidays.append(col)

        processed_data = convert_to_processed_format(vacations, holidays)

        firefighter_entry = {
            "idnum": None,  # No ID in Telestaff export, so we set it to None
            "fname": first_name.capitalize(),
            "lname": last_name.capitalize(),
            "name": f"{first_name}, {last_name[0]} (ID: 'None')",  # Placeholder format for JSON consistency
            "rank": str(row['Rank']).strip(),
            "shift": shift,  # Store the cleaned shift
            "hireDate": None,  # Not present in Telestaff export
            "max_days_off": None,  # Default to None
            "used_vacation_days": None,
            "used_holiday_days": None,
            "approved_days_count": None,
            "picks": [],
            "processed": processed_data,
            "hr_validations": {},  # Empty for now
            "exclusions": []
        }

        results.append(firefighter_entry)

    return results


# Example usage:
if __name__ == "__main__":
    excel_file = "./telestaff_to_json/raw_telestaff_exports/Multiday Roster Report - A Shift - 02-01-2025 through 01-31-2026.xlsx"
    data = read_telestaff_export(excel_file)
    for entry in data:
        print(entry)
