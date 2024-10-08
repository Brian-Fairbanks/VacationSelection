# file_io.py
import csv
import logger

def read_firefighter_data(filename, date_format):
    print("OPENING DATA")
    from firefighter import FFighter, Pick  # Import classes as needed
    from validation import ensure_rank  # Import validation function
    from datetime import datetime

    ffdata = []
    try:
        # Step 1: Attempt to open the file
        with open(filename, mode="r", encoding="utf-8-sig") as csvfile:
            print(f"Successfully opened file: {filename}")

            # Step 2: Create the CSV reader and read the headers
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            print(f"File headers: {headers}")

            # Check if required headers exist
            required_headers = ['First Name', 'Last Name', 'Rank', 'Employee Start Date', 'Shift']
            for header in required_headers:
                if header not in headers:
                    raise ValueError(f"Missing required header: {header}")

            # Step 3: Read each row from the CSV
            for index, row in enumerate(reader):
                try:
                    # Step 3.1: Log each row being processed
                    print(f"Processing row {index + 1}: {row}")

                    fname = row['First Name']
                    lname = row['Last Name']
                    rank = ensure_rank(row["Rank"])

                    # Step 3.2: Handle potential issues with missing data
                    if not fname or not lname or not rank:
                        print(f"Row {index + 1} skipped due to missing critical information.")
                        continue

                    # Step 3.3: Parse hire date and shift
                    startDate = datetime.strptime(row['Employee Start Date'], date_format).date()
                    shift = row["Shift"]

                    # Step 3.4: Process pick dates
                    pick_dates = []
                    for x in range(1, 40):
                        day_key = f"Day {x}"
                        if row[day_key]:
                            try:
                                pick_date = datetime.strptime(row[day_key], date_format).date()
                                pick_dates.append(Pick(pick_date, "U"))
                            except Exception as e:
                                print(f"Failed to parse pick date '{row[day_key]}' in row {index + 1}: {e}")
                                continue

                    # Step 3.5: Add firefighter to the list
                    ffdata.append(FFighter(fname, lname, startDate, rank, shift, pick_dates))
                
                except Exception as e:
                    # Handle any exceptions for individual rows without breaking the entire loop
                    print(f"Failed to process row {index + 1}: {e}")

            print("Finished reading firefighter data.")

    except Exception as e:
        print(f"Failed to read file: {e}")

    return ffdata

def write_calendar_to_csv(calendar, suffix, write_path, runtime):
    with open(f'{write_path}/{runtime}-calendar-{suffix}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Date', "First", "Second", "Third", "Fourth", "Fifth"]
        writer.writerow(header)
        for key in sorted(calendar.keys()):
            writer.writerow([key] + calendar[key])