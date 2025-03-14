from datetime import datetime
from fuzzywuzzy import fuzz  # import fuzzy matching
from .file_io import parse_date
from vacation_selection.setup_logging import setup_logging

# Set up runtime and logging
runtime = datetime.now().strftime("%Y.%m.%d %H.%M")
write_path = ".//output"
logger = setup_logging(f"RunLog-{runtime}.log", base=write_path, debug=False)
print = logger.info

from .file_io import (
    read_firefighter_data, write_calendar_to_csv, 
    write_picks_to_csv, print_final, write_ffighters_to_json, read_hr_validation
)
from .firefighter import FFighter
from .priority import set_priorities
from .cal import make_calendar
from vacation_selection.validation import ensure_rank  # Import validation function


def parse_name(name_str):
    """
    Parses a string into (first, middle, last).
    Supports the format "LastName, FirstName MiddleName" 
    or simple fallbacks like "First Last" if no comma.
    Returns (first, middle, last) as strings (may be empty if missing).
    """
    name_str = (name_str or "").strip()
    if not name_str:
        return "", "", ""

    if ',' in name_str:
        # e.g. "Obiedo, Salvador Gabriel"
        last_part, first_part = name_str.split(',', 1)
        last_part = last_part.strip()
        parts = first_part.strip().split()
        if len(parts) == 1:
            first, middle = parts[0], ""
        else:
            first = parts[0]
            middle = " ".join(parts[1:])
        return first, middle, last_part
    else:
        # Fallback: assume "First Middle Last" or "First Last"
        parts = name_str.split()
        if len(parts) == 1:
            return parts[0], "", ""
        elif len(parts) == 2:
            return parts[0], "", parts[1]
        else:
            return parts[0], " ".join(parts[1:-1]), parts[-1]


def average_top_2_fuzzy_score(ff, hr_name_str):
    """
    Given a Firefighter object `ff` with .fname, .mname (optional), .lname,
    and a raw HR name string (e.g. "Obiedo, Salvador Gabriel"),
    parse both and compute the average of the top 2 fuzzy‐match scores.
    """
    # Parse FF name (assuming ff.fname, ff.lname exist; mname optional)
    ff_first = (ff.fname or "").strip()
    ff_middle = (getattr(ff, 'mname', None) or "").strip()
    ff_last = (ff.lname or "").strip()

    # Parse HR name
    hr_first, hr_middle, hr_last = parse_name(hr_name_str)

    # Build combos for FF
    combos_ff = [
        f"{ff_first} {ff_last}".strip(),                # e.g. "Salvador Obiedo"
        f"{ff_first} {ff_middle} {ff_last}".strip()     # e.g. "Salvador Gabriel Obiedo"
    ]
    # Build combos for HR
    combos_hr = [
        f"{hr_first} {hr_last}".strip(),                # e.g. "Salvador Obiedo"
        f"{hr_first} {hr_middle} {hr_last}".strip()     # e.g. "Salvador Gabriel Obiedo"
    ]

    # Compute fuzzy scores across all combos
    scores = []
    for ff_combo in combos_ff:
        for hr_combo in combos_hr:
            if ff_combo and hr_combo:
                score = fuzz.ratio(ff_combo.upper(), hr_combo.upper())
                scores.append(score)

    # Sort descending, average top 2
    scores.sort(reverse=True)
    if not scores:
        return 0
    elif len(scores) == 1:
        return scores[0]
    else:
        return (scores[0] + scores[1]) / 2.0
    
def find_hr_record(ff, hr_data, threshold=80):
    """
    1) If ff.idnum is valid (non-zero), try an ID match first.
    2) Otherwise, do a fuzzy name match with average_top_2_fuzzy_score.
    """
    # 1) ID-based match
    if ff.idnum and str(ff.idnum).strip() not in ["0", ""]:
        hr_record = next(
            (hr for hr in hr_data if str(hr['Employee Number']).strip() == str(ff.idnum).strip()),
            None
        )
        if hr_record:
            return hr_record

    # 2) Fuzzy name-based match
    best_match = None
    best_score = 0

    for hr in hr_data:
        raw_name = hr.get("Employee Name", "").strip()
        if not raw_name:
            continue
        avg_score = average_top_2_fuzzy_score(ff, raw_name)
        if avg_score > best_score:
            best_score = avg_score
            best_match = hr

    if best_score >= threshold and best_match:
        logger.info(f"Fuzzy match for {ff.fname} {ff.lname} -> {best_match.get('Employee Name','Unknown')} (Score: {best_score})")
        return best_match
    else:
        logger.warning(f"No acceptable fuzzy match for {ff.fname} {ff.lname} (Best Score: {best_score})")
        return None



def validate_against_hr(ffighters, hr_data):
    """
    Validates firefighter data against HR data, checking Hire Date, Vacation Hours, Holiday Hours, and Rank.
    Returns a list of validated firefighter objects.
    """
    validated_ffighters = []
    
    for ff in ffighters:
        # Initialize hr_validations dictionary
        ff.hr_validations = {}

        # Find corresponding HR record, first by idnum then by fuzzy name matching
        hr_record = find_hr_record(ff, hr_data)
        
        if hr_record:
            # Ensure ID Num
            hr_id_num = hr_record.get('Employee Number', 0)
            if int(ff.idnum) != int(hr_id_num):
                logger.warning(
                    f"ID Num mismatch for {ff.name} (ID: {ff.idnum}): {ff.idnum} - Overwriting with {hr_id_num} from HR data."
                )
                ff.hr_validations['ID Num'] = (ff.idnum, hr_id_num)
                ff.idnum = hr_id_num

            # Validate Hire Date
            hire_date = parse_date(hr_record['Hire Date'])  # Use parse_date here
            if ff.hireDate != hire_date:
                logger.warning(f"Hire Date mismatch for {ff.name} (ID: {ff.idnum}):   {ff.hireDate} - Overwriting with {hire_date} from HR data.")
                ff.hr_validations['Hire Date'] = (ff.hireDate, hire_date)
                ff.hireDate = hire_date
            
            # Validate Vacation and Holiday Hours
            hr_vacation_hours = int(hr_record.get('# of Vacation Leave Hours awarded', 0))
            hr_holiday_hours = int(hr_record.get('# of Holiday Leave Hours awarded', 0))
            hr_vacation_days = hr_vacation_hours / 24
            hr_holiday_days = hr_holiday_hours / 24

            # Check awarded vacation days
            if ff.awarded_vacation_days != hr_vacation_days:
                logger.warning(f"Vacation days mismatch for {ff.name} (ID: {ff.idnum}):   {ff.awarded_vacation_days} - Overwriting with {hr_vacation_days} from HR data.")
                ff.hr_validations['Vacation Days'] = (ff.awarded_vacation_days, hr_vacation_days)
                ff.awarded_vacation_days = hr_vacation_days

            # Check awarded holiday days
            if ff.awarded_holiday_days != hr_holiday_days:
                logger.warning(f"Holiday days mismatch for {ff.name} (ID: {ff.idnum}):   {ff.awarded_holiday_days} - Overwriting with {hr_holiday_days} from HR data.")
                ff.hr_validations['Holiday Days'] = (ff.awarded_holiday_days, hr_holiday_days)
                ff.awarded_holiday_days = hr_holiday_days

            # Check Max Days Off
            hr_total_allowed_day_count = int((hr_vacation_hours + hr_holiday_hours) / 24)
            
            # Convert both values to integers for a proper comparison
            if int(ff.max_days_off) != hr_total_allowed_day_count:
                logger.warning(f"Max Days Off mismatch for {ff.name} (ID: {ff.idnum}):   {ff.max_days_off} - Overwriting with {hr_total_allowed_day_count} from HR data.")
                ff.hr_validations['Max Days Off'] = (ff.max_days_off, hr_total_allowed_day_count)
                ff.max_days_off = hr_total_allowed_day_count

            # Validate Rank
            hr_rank = ensure_rank(hr_record.get('Rank', '').strip())
            if ff.rank != hr_rank:
                logger.warning(f"Rank mismatch for {ff.name} (ID: {ff.idnum}):   {ff.rank} - Overwriting with {hr_rank} from HR data.")
                ff.hr_validations['Rank'] = (ff.rank, hr_rank)
                ff.rank = hr_rank
            
            # If all checks pass, add firefighter to validated list
            validated_ffighters.append(ff)
        else:
            logger.warning(f"No matching HR record found for {ff.name} (ID: {ff.idnum}).")

    return validated_ffighters



def main(pick_filename, hr_filename, format):
    date_format = '%m-%d-%Y'
    
    try:
        # Import Firefighter File
        ffighters = read_firefighter_data(pick_filename, date_format, format)

        # Validate Firefighter Data against HR File
        hr_data = read_hr_validation(hr_filename)
        ffighters = validate_against_hr(ffighters, hr_data)

        # Set Priorities for Firefighters
        ffighters = set_priorities(ffighters)

    except Exception as e:
        logger.error(f"ERROR: {e}")
        exit(1)

    # Check if firefighter list is empty after import and validation
    if not ffighters:
        logger.error("\nNo firefighter data available to process.")
        exit(1)

    # Work in shifts
    for shift in ["A", "B", "C"]:
        shift_members = [ff for ff in ffighters if ff.shift == shift]
        results = make_calendar(shift_members)

        # Write outputs
        write_ffighters_to_json(shift_members, f'{shift}_ffighters', write_path, runtime)
        write_calendar_to_csv(results['calendar'], shift, write_path, runtime)
        write_picks_to_csv(shift_members, shift, write_path, runtime)
        print_final(shift_members)

if __name__ == '__main__':
    main('firefighter_data.csv', 'hr_data.csv', 'some_format')
