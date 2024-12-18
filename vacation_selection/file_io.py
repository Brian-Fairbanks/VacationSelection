# file_io.py
import csv
import json
import os
import pandas as pd
from datetime import datetime, date
import vacation_selection.setup_logging as setup_logging
from vacation_selection.firefighter import FFighter, Pick
from vacation_selection.cal import Day
from vacation_selection.validation import ensure_rank  # Import validation function

logger = setup_logging.setup_logging()

# ================================================================================
# Reading from CSV
# ================================================================================

def read_firefighter_data(filename, date_format, file_format):
    """Reads firefighter data from a CSV file and processes it based on the specified file format."""
    ffdata = []
    try:
        with open(filename, mode="r", encoding="utf-8-sig") as csvfile:
            logger.debug(f"Successfully opened file: {filename}")

            # Create the CSV reader and read the headers
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            logger.debug(f"File headers: {headers}")

            logger.debug(f"Processing data for File Format: {file_format}")
            # Read each row based on the specified file format
            if file_format == 2024:
                ffdata = process_firefighter_data_2024(reader, date_format)
            elif file_format == 2025:
                ffdata = process_firefighter_data_2025(reader, date_format)
            else:
                raise ValueError("Unsupported file format year.")
            logger.debug("Finished reading firefighter data.")

    except Exception as e:
        logger.error(f"Failed to read file: {e}")

    return ffdata

# ================================================================================
# Reading Exclusions File
# ================================================================================

def read_exclusions_file(file_path):
    """
    Reads exclusions data from an Excel file, processes combined 'LName,FName' column,
    and returns a list of dictionaries with standardized fields.
    """
    exclusions = []
    try:
        logger.info(f"Reading exclusions file: {file_path}")
        exclusions_df = pd.read_excel(file_path, parse_dates=['Leave Start', 'Leave End'])

        # Log column names for debugging
        logger.debug(f"Exclusions file columns: {exclusions_df.columns.tolist()}")

        # Check if the problematic 'LName,FName' column exists
        if 'LName,FName' in exclusions_df.columns:
            logger.info("Splitting combined 'LName,FName' column into 'LName' and 'FName'")
            exclusions_df[['LName', 'FName']] = exclusions_df['LName,FName'].str.split(',', expand=True)
            
            # Strip whitespace from the new columns
            exclusions_df['LName'] = exclusions_df['LName'].str.strip()
            exclusions_df['FName'] = exclusions_df['FName'].str.strip()

            # Drop the original combined column
            exclusions_df.drop(columns=['LName,FName'], inplace=True)
        
        # Standardize column names
        exclusions_df.columns = exclusions_df.columns.str.strip()

        # Validate required columns
        required_columns = ['LName', 'FName', 'Leave Start', 'Reason']
        for col in required_columns:
            if col not in exclusions_df.columns:
                raise ValueError(f"Missing required column '{col}' in exclusions file.")

        # Handle optional 'Leave End' column
        if 'Leave End' not in exclusions_df.columns:
            logger.warning("Column 'Leave End' not found. Setting to None for all rows.")
            exclusions_df['Leave End'] = None

        # Replace NaT in 'Leave End' with None
        exclusions_df['Leave End'] = exclusions_df['Leave End'].where(pd.notna(exclusions_df['Leave End']), None)

        # Convert to dictionary records
        exclusions = exclusions_df.to_dict(orient='records')
        logger.info(f"Loaded {len(exclusions)} exclusions from {file_path}")
    except Exception as e:
        logger.error(f"Failed to read exclusions file: {e}")
        raise Exception(f"Error reading exclusions file: {e}")
    return exclusions


# Helper functions to process CSV data
# ================================================================================
def process_firefighter_data_2024(reader, date_format):
    """Processes firefighter data in the 2024 format."""
    logger.debug("Starting 2024 data processing")
    ffdata = []
    for index, row in enumerate(reader):
        try:
            fname = row['First Name']
            lname = row['Last Name']
            rank = ensure_rank(row["Rank"])
            idnum = row['Employee ID #']
            startDate = parse_date(row['Employee Start Date'])
            shift = row["Shift"]

            pick_dates = []
            for x in range(1, 18):
                day_key = f"Day {x}"
                type_key = f"Type {x}" if x != 1 else " Type"
                if day_key in row and row[day_key]:
                    try:
                        pick_date = parse_date(row[day_key])
                        pick_type = row.get(type_key, "Unaddressed")
                        pick_dates.append(Pick(pick_date, type=pick_type))
                    except Exception as e:
                        logger.error(f"Failed to parse pick date '{row[day_key]}' in row {index + 1}: {e}")
                        continue

            ffdata.append(FFighter(idnum, fname, lname, startDate, rank, shift, pick_dates))

        except Exception as e:
            logger.error(f"Failed to process row {index + 1}: {e}")

    return ffdata

def process_firefighter_data_2025(reader, date_format):
    """Processes firefighter data in the 2025 format."""
    logger.debug("Starting 2025 data processing")
    ffdata = []
    for index, row in enumerate(reader):
        try:
            logger.debug(f"Processing row {index + 1}: {row}")

            # Parse basic firefighter data
            try:
                fname = row['First Name']
                lname = row['Last Name']
                rank = ensure_rank(row["Rank"])
                idnum = row['Employee ID #']
                startDate = parse_date(row['Employee Hire Date'])
                shift = row["Shift"]
                logger.debug(f"Parsed data - Name: {fname} {lname}, Rank: {rank}, ID: {idnum}, Start Date: {startDate}, Shift: {shift}")
            except KeyError as ke:
                logger.error(f"Missing key in row {index + 1}: {ke}. Row: {row}")
                continue
            except ValueError as ve:
                logger.error(f"Invalid value in row {index + 1}: {ve}. Row: {row}")
                continue

            # Check acknowledgment of form completion
            acknowledgment = row.get('Acknowledgment of Form Completion', '').strip()
            
            # If the user prefers to skip the selection, do not add any picks
            if acknowledgment == "I would prefer to skip the selection, and submit a blank request form.":
                logger.info(f"Skipping pick selection for {fname} {lname} (ID: {idnum}) as per acknowledgment.")
                pick_dates = []  # No picks are added
            else:
                # Parse pick dates and shifts if the user continues with the selection
                pick_dates = []
                for x in range(1, 41):
                    day_key = f"Day {x}"
                    shift_key = f"Shift Selection {x}"
                    if day_key in row and row[day_key]:
                        try:
                            pick_date = parse_date(row[day_key])
                            shift_selection = row.get(shift_key, 'AMPM')
                            pick_dates.append(Pick(pick_date, increments=shift_selection))
                            logger.debug(f"Added pick - Date: {pick_date}, Shift: {shift_selection} for {fname} {lname}")
                        except ValueError as ve:
                            logger.error(f"Failed to parse pick date '{row[day_key]}' in row {index + 1}: {ve}")
                            continue

            # Create FFighter instance
            ffighter = FFighter(idnum, fname, lname, startDate, rank, shift, pick_dates)
            logger.debug(f"Created FFighter instance: {ffighter}")

            ffdata.append(ffighter)

        except Exception as e:
            logger.error(f"Unhandled error processing row {index + 1}: {e}. Row: {row}")
            # Optionally, include stack trace for deeper debugging
            logger.exception(e)
    return ffdata


# Helper function to parse dates from strings
def parse_date(date_value):
    """Parses a date from various input types, including strings and pandas Timestamps."""
    from pandas import Timestamp

    # If the value is already a Timestamp, convert it to a date
    if isinstance(date_value, Timestamp):
        return date_value.date()

    # If the value is a string, parse it
    if isinstance(date_value, str):
        possible_formats = [
            '%Y-%m-%d %H:%M:%S',  # e.g., 2024-11-15 08:53:32
            '%Y-%m-%d %H:%M',     # e.g., 2024-11-15 08:53
            '%Y-%m-%d',           # e.g., 2024-11-15
            '%m-%d-%Y',           # e.g., 11-15-2024
            '%m/%d/%Y',           # e.g., 11/15/2024
            '%d-%m-%Y',           # e.g., 15-11-2024
            '%d/%m/%Y'            # e.g., 15/11/2024
        ]
        for fmt in possible_formats:
            try:
                return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format for '{date_value}'")

    # If the value is not a recognized type, raise an error
    raise TypeError(f"Unsupported date type: {type(date_value)}")



# Read in the HR_Validation File
def read_hr_validation(filename):
    """Reads HR validation data from an Excel file and returns it as a list of dictionaries."""
    hr_data = []
    try:
        # Read the .xlsx file using pandas
        df = pd.read_excel(filename, engine='openpyxl')

        # Convert DataFrame to a list of dictionaries
        hr_data = df.to_dict(orient='records')
        logger.debug(f"Successfully read HR validation file: {filename}")
        
    except Exception as e:
        logger.error(f"Failed to read HR validation file: {e}")

    return hr_data

# ================================================================================
# Writing Outputs
# ================================================================================

def write_calendar_to_csv(calendar, suffix, write_path, runtime):
    with open(f'{write_path}/{runtime}-calendar-{suffix}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        header = Day.get_header()
        writer.writerow(header)

        for date in sorted(calendar.keys()):
            calendar[date].write_to_row(writer)

def print_final(ffighters):
    """Prints the final results for each firefighter."""
    print('\n\n  --==  Final Results   ==--\n')
    for ffighter in ffighters:
        # Include ID in the name for clarity
        print(f'{ffighter.name:<20} (ID: {ffighter.idnum}): \n  Started:{ffighter.hireDate} - ({ffighter.shift} shift) {ffighter.rank}')
        for key in ffighter.processed:
            print(key)


def write_picks_to_csv(ffighters, suffix, write_path, runtime):
    """Writes the picks and status of each firefighter to a CSV file."""
    file_name = f'{write_path}/{runtime}-FFighters-{suffix}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Name (ID)', "Rank", "Date Requested", "Type", "Increments", "Determination", "Reason"]
        writer.writerow(header)

        for ffighter in ffighters:
            # Include ID in the name for clarity
            writer.writerow([f'{ffighter.name} (ID: {ffighter.idnum})', ffighter.rank])
            for key in ffighter.processed:
                writer.writerow([
                    '', '', key.date, key.type,
                    key.increments_plain_text(), key.determination, key.reason
                ])
            writer.writerow([])

# ==========    JSON    ==============================================================

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()  # Convert `date` to a string in ISO 8601 format
        return super().default(obj)
    
def write_ffighters_to_json(ffighters, suffix, write_path, runtime):
    """Writes the firefighter list and their processed picks to a JSON file."""
    # Include ID in the name field in the dictionary representation
    ffighter_data = [
        {**ffighter.to_dict(), "name": f"{ffighter.name} (ID: {ffighter.idnum})"} 
        for ffighter in ffighters
    ]
    file_name = f"{write_path}/{runtime}-FFighters-{suffix}.json"

    with open(file_name, 'w') as json_file:
        # Use the custom encoder to handle `date` serialization
        json.dump(ffighter_data, json_file, indent=4, cls=CustomJSONEncoder)

def read_ffighters_from_json(file_path):
    """Reads firefighter data from a JSON file and returns a list of FFighter objects."""
    ffighter_list = []
    try:
        with open(file_path, 'r') as json_file:
            ffighter_dicts = json.load(json_file)
            ffighter_list = [FFighter.from_dict(ff_dict) for ff_dict in ffighter_dicts]
    except Exception as e:
        logger.error(f"Failed to read from JSON: {e}")

    return ffighter_list

def write_analysis_to_json(analysis, write_path, runtime):
    """
    Writes the analysis data to a JSON file in the specified output folder.
    """
    try:
        # Ensure the write path exists
        os.makedirs(write_path, exist_ok=True)

        # Construct file name
        file_name = f"{write_path}/{runtime}-analysis.json"
        
        # Write JSON data
        with open(file_name, 'w') as json_file:
            json.dump(analysis, json_file, indent=4, cls=CustomJSONEncoder)
        logger.info(f"Analysis data saved to {file_name}")
    except Exception as e:
        logger.error(f"Failed to write analysis data to JSON: {e}")
        raise

def read_analysis_from_json(output_folder):
    """
    Loads the most recent analysis JSON file from the specified output folder.
    Returns None if no valid analysis file is found.
    """
    try:
        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            logger.warning(f"Output folder '{output_folder}' does not exist.")
            return None

        # Get all analysis files
        analyze_files = [
            f for f in os.listdir(output_folder) if f.endswith("-analysis.json")
        ]
        
        if not analyze_files:
            logger.warning("No analysis files found.")
            return None

        # Sort files by modification time (newest first)
        analyze_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_folder, x)), reverse=True)
        latest_file = os.path.join(output_folder, analyze_files[0])

        # Read and return JSON data
        with open(latest_file, 'r') as json_file:
            analysis_data = json.load(json_file)
        logger.info(f"Loaded analysis file: {latest_file}")
        return analysis_data
    except Exception as e:
        logger.error(f"Failed to load analysis data: {e}")
        return None


def write_calendar_to_csv(calendar, suffix, write_path, runtime):
    """Writes the calendar data to a CSV file."""
    file_name = f'{write_path}/{runtime}-calendar-{suffix}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        header = Day.get_header()
        writer.writerow(header)

        for date in sorted(calendar.keys()):
            calendar[date].write_to_row(writer)
