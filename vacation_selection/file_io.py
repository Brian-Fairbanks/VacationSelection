# file_io.py
import csv
import json
import pandas as pd
from datetime import datetime
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
            fname = row['First Name']
            lname = row['Last Name']
            rank = ensure_rank(row["Rank"])
            idnum = row['Employee ID #']
            startDate = parse_date(row['Employee Hire Date'])
            shift = row["Shift"]

            pick_dates = []
            for x in range(1, 41):
                day_key = f"Day {x}"
                shift_key = f"Shift Selection {x}"
                if day_key in row and row[day_key]:
                    try:
                        pick_date = parse_date(row[day_key])
                        pick_dates.append(Pick(pick_date, increments=row.get(shift_key)))
                    except Exception as e:
                        logger.error(f"Failed to parse pick date '{row[day_key]}' in row {index + 1}: {e}")
                        continue

            ffdata.append(FFighter(idnum, fname, lname, startDate, rank, shift, pick_dates))

        except Exception as e:
            logger.error(f"Failed to process row {index + 1}: {e}")

    return ffdata

# Helper function to parse dates from strings
def parse_date(date_str):
    """Try to parse a date string in multiple formats until one works."""
    possible_formats = [
        '%m-%d-%Y',  # e.g., 06-11-2009
        '%m/%d/%Y',  # e.g., 06/11/2009
        '%Y-%m-%d',  # e.g., 2009-06-11
        '%d-%m-%Y',  # e.g., 11-06-2009
        '%d/%m/%Y'   # e.g., 11/06/2009
    ]
    for fmt in possible_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format for '{date_str}' not recognized.")


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
        print(f'{ffighter.name:<20} ({ffighter.idnum}): \n  Started:{ffighter.hireDate} - ({ffighter.shift} shift) {ffighter.rank}')
        for key in ffighter.processed:
            print(key)


def write_picks_to_csv(ffighters, suffix, write_path, runtime):
    """Writes the picks and status of each firefighter to a CSV file."""
    file_name = f'{write_path}/{runtime}-FFighters-{suffix}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Name', "Rank", "Date Requested", "Type", "Increments", "Determination", "Reason"]
        writer.writerow(header)

        for ffighter in ffighters:
            writer.writerow([ffighter.name, ffighter.rank])
            for key in ffighter.processed:
                writer.writerow([
                    '', '', key.date, key.type,
                    key.increments_plain_text(), key.determination, key.reason
                ])
            writer.writerow([])

def write_ffighters_to_json(ffighters, suffix, write_path, runtime):
    """Writes the firefighter list and their processed picks to a JSON file."""
    ffighter_data = [ffighter.to_dict() for ffighter in ffighters]
    file_name = f"{write_path}/{runtime}-FFighters-{suffix}.json"

    with open(file_name, 'w') as json_file:
        json.dump(ffighter_data, json_file, indent=4)

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

def write_calendar_to_csv(calendar, suffix, write_path, runtime):
    """Writes the calendar data to a CSV file."""
    file_name = f'{write_path}/{runtime}-calendar-{suffix}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        header = Day.get_header()
        writer.writerow(header)

        for date in sorted(calendar.keys()):
            calendar[date].write_to_row(writer)
