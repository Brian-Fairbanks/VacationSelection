# read_telestaff_export.py
import pandas as pd

def read_telestaff_export(excel_path):
    """
    Reads a Telestaff export file with the following layout:
      - Row 1 (index 0): Title (discard)
      - Row 2 (index 1): Report type (discard)
      - Row 3 (index 2): Date range, e.g., "2/01/2025 through 1/31/2026"
      - Row 4 (index 3): Variable settings (discard)
      - Row 5 (index 4): Data header for columns E onward (e.g., calendar days in M/D format)
      - Rows 6 onward (index >=5): Data rows:
           Column A: Shift (repeats downward)
           Column B: Unused
           Column C: Rank (carries down)
           Column D: Name in the format "LNAME, FNAME (vehicles ...)"
           Columns E onward: Codes for that day (e.g., "V" for vacation, "H" for holiday,
                         ignoring other codes like *V, *H, .V, .H)
    
    Returns:
      A list of dictionaries, one per data row, with keys:
         - shift: str
         - rank: str
         - first_name: str
         - last_name: str
         - vacations: list of full date strings (YYYY-MM-DD)
         - holidays: list of full date strings (YYYY-MM-DD)
    """
    # Read the entire Excel file without headers.
    df_full = pd.read_excel(excel_path, header=None)
    
    # --- Extract the date range from row 3 (index 2) ---
    date_range_str = df_full.iloc[2, 0]
    # Expecting format like "2/01/2025 through 1/31/2026"
    try:
        start_date_str, _, end_date_str = date_range_str.partition(" through ")
        start_date = pd.to_datetime(start_date_str.strip(), format='%m/%d/%Y')
        end_date = pd.to_datetime(end_date_str.strip(), format='%m/%d/%Y')
    except Exception as e:
        raise ValueError(f"Failed to parse date range from row 3: {date_range_str}") from e
    
    # --- Extract day headers from row 5 (index 4) for columns E onward ---
    data_header = df_full.iloc[4, :]
    # For columns 0-3 we assign fixed names; for columns 4 onward, use the header from the file.
    # These headers are expected to be in M/D format (e.g., "2/3") and we will convert them to full dates.
    raw_day_headers = data_header.iloc[4:].tolist()
    full_day_headers = []
    for dh in raw_day_headers:
        try:
            # Parse month/day; note that if parsed with no year, default year is 1900.
            parsed = pd.to_datetime(str(dh).strip(), format='%m/%d', errors='coerce')
            if pd.isna(parsed):
                full_day_headers.append(None)
            else:
                # Replace year with the start_date's year.
                parsed = parsed.replace(year=start_date.year)
                # If the parsed date is before the start_date, assume it belongs to the next year.
                if parsed < start_date:
                    parsed = parsed.replace(year=start_date.year + 1)
                full_day_headers.append(parsed.strftime('%Y-%m-%d'))
        except Exception:
            full_day_headers.append(None)
    
    # --- Data rows start from row 6 (index 5) ---
    df_data = df_full.iloc[5:, :].copy()
    
    # Define columns: first 4 fixed; then use our full_day_headers for columns 5 onward.
    fixed_columns = ['Shift', 'Unused', 'Rank', 'Name']
    all_columns = fixed_columns + full_day_headers
    # Make sure the number of columns in df_data matches the length of all_columns.
    df_data = df_data.iloc[:, :len(all_columns)]
    df_data.columns = all_columns
    
    # Forward-fill Shift and Rank columns.
    df_data['Shift'] = df_data['Shift'].ffill()
    df_data['Rank'] = df_data['Rank'].ffill()
    
    results = []
    # Process each row
    for idx, row in df_data.iterrows():
        # Skip rows with missing Name or where Name equals one of the header labels (e.g., "CALENDARDATE")
        name_field = row['Name']
        if pd.isna(name_field) or str(name_field).upper().strip() == "CALENDARDATE":
            continue
        
        shift = row['Shift']
        rank = row['Rank']
        
        # Parse the Name field expecting "LNAME, FNAME (vehicles ...)"
        name_str = str(name_field)
        parts = name_str.split(',')
        last_name = parts[0].strip() if parts else ""
        first_name = ""
        if len(parts) > 1:
            first_name = parts[1].split('(')[0].strip()
        
        vacations = []
        holidays = []
        
        # For each day column (which now has a full date string as its header)
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
        
        results.append({
            "shift": str(shift).strip(),
            "rank": str(rank).strip(),
            "first_name": first_name,
            "last_name": last_name,
            "vacations": vacations,
            "holidays": holidays
        })
    
    return results

# Example usage:
if __name__ == "__main__":
    excel_file = "./telestaff_to_json/raw_telestaff_exports/Multiday Roster Report - A Shift - 02-01-2025 through 01-31-2026.xlsx"
    data = read_telestaff_export(excel_file)
    for entry in data:
        print(entry)
