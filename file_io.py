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
        with open(filename, mode="r", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                fname = row['First Name']
                lname = row['Last Name']
                rank = ensure_rank(row["Rank"])
                startDate = datetime.strptime(row['Employee Start Date'], date_format).date()
                shift = row["Shift"]
                pick_dates = [
                    Pick(datetime.strptime(row[f"Day {x}"], date_format).date(), "U")
                    for x in range(1, 40) if row[f"Day {x}"]
                ]
                ffdata.append(FFighter(fname, lname, startDate, rank, shift, pick_dates))
    except Exception as e:
        print(f"failed to read file:{e}")
    return ffdata

def write_calendar_to_csv(calendar, suffix, write_path, runtime):
    with open(f'{write_path}/{runtime}-calendar-{suffix}.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Date', "First", "Second", "Third", "Fourth", "Fifth"]
        writer.writerow(header)
        for key in sorted(calendar.keys()):
            writer.writerow([key] + calendar[key])
