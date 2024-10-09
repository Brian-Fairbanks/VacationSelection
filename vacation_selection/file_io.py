# file_io.py
import csv
import vacation_selection.setup_logging as setup_logging
from vacation_selection.validation import ensure_rank  # Import validation function
from datetime import datetime

from vacation_selection.firefighter import FFighter, Pick  # Import classes as needed
from datetime import datetime

logger = setup_logging.setup_logging()

# ================================================================================
# Reading
# ================================================================================

def read_firefighter_data(filename, date_format, file_format):

    ffdata = []
    try:
        # Step 1: Attempt to open the file
        with open(filename, mode="r", encoding="utf-8-sig") as csvfile:
            logger.debug(f"Successfully opened file: {filename}")

            # Step 2: Create the CSV reader and read the headers
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            logger.debug(f"File headers: {headers}")

            # Check if required headers exist
            required_headers = ['First Name', 'Last Name', 'Rank', 'Employee Start Date', 'Shift']
            for header in required_headers:
                if header not in headers:
                    raise ValueError(f"Missing required header: {header}")

            logger.debug(f"Processing data for File Format: {file_format}")
            # Step 3: Read each row from the CSV based on file format
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

# Reading Sub Modules
# ========================
def process_firefighter_data_2024(reader, date_format):
    logger.debug("starting: 2024")
    ffdata = []
    for index, row in enumerate(reader):
        try:
            logger.debug(f"Processing row {index + 1}: {row}")

            fname = row['First Name']
            lname = row['Last Name']
            rank = ensure_rank(row["Rank"])
            id = row['Employee ID #']

            if not fname or not lname or not rank:
                logger.debug(f"Row {index + 1} skipped due to missing critical information.")
                continue

            startDate = datetime.strptime(row['Employee Start Date'], date_format).date()
            shift = row["Shift"]

            pick_dates = []
            for x in range(1, 18):
                day_key = f"Day {x}"
                type_key = f"Type {x}" if x != 1 else " Type"
                if day_key in row and row[day_key]:
                    try:
                        pick_date = datetime.strptime(row[day_key], date_format).date()
                        pick_type = row.get(type_key, "U")
                        pick_dates.append(Pick(pick_date, pick_type))
                    except Exception as e:
                        logger.error(f"Failed to parse pick date '{row[day_key]}' in row {index + 1}: {e}")
                        continue

            ffdata.append(FFighter(fname, lname, id, startDate, rank, shift, pick_dates))
        
        except Exception as e:
            logger.error(f"Failed to process row {index + 1}: {e}")

    return ffdata



def process_firefighter_data_2025(reader, date_format):
    ffdata = []
    for index, row in enumerate(reader):
        try:
            logger.debug(f"Processing row {index + 1}: {row}")

            fname = row['First Name']
            lname = row['Last Name']
            rank = ensure_rank(row["Rank"])

            if not fname or not lname or not rank:
                logger.debug(f"Row {index + 1} skipped due to missing critical information.")
                continue

            startDate = datetime.strptime(row['Employee Start Date'], date_format).date()
            shift = row["Shift"]

            pick_dates = []
            for x in range(1, 40):  # Assuming the 2025 format is similar to 2024
                day_key = f"Day {x}"
                if day_key in row and row[day_key]:
                    try:
                        pick_date = datetime.strptime(row[day_key], date_format).date()
                        pick_dates.append(Pick(pick_date, "U"))
                    except Exception as e:
                        logger.debug(f"Failed to parse pick date '{row[day_key]}' in row {index + 1}: {e}")
                        continue

            ffdata.append(FFighter(fname, lname, startDate, rank, shift, pick_dates))
        
        except Exception as e:
            logger.error(f"Failed to process row {index + 1}: {e}")

    return ffdata

# ================================================================================
# Writing Outputs
# ================================================================================

def write_calendar_to_csv(calendar, suffix, write_path, runtime):
    with open(f'{write_path}/{runtime}-calendar-{suffix}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Date', "First", "Second", "Third", "Fourth", "Fifth"]
        writer.writerow(header)
        for key in sorted(calendar.keys()):
            writer.writerow([key] + calendar[key])


def print_final(ffighters):
    """Prints the final results for each firefighter."""
    print('\n\n  --==  Final Results   ==--\n')
    for ffighter in ffighters:
        print(f'{ffighter.name:<20} ({ffighter.id}): \n  Started:{ffighter.hireDate} - ({ffighter.shift} shift) {ffighter.rank}')
        for key in ffighter.processed:
            print(key)


def write_picks_to_csv(ffighters, suffix, write_path, runtime):
    """Writes the picks and status of each firefighter to a CSV file."""
    with open(f'{write_path}/{runtime}-FFighters-{suffix}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Name', "Rank", "Date Requested", "Type", "Determination", "Reason"]
        writer.writerow(header)

        for ffighter in ffighters:
            writer.writerow([ffighter.name, ffighter.rank])
            for key in ffighter.processed:
                writer.writerow(['', '', key.date, key.type, key.determination, key.reason])
            writer.writerow([])