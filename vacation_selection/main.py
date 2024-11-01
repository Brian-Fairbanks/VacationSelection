from datetime import datetime
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

def validate_against_hr(ffighters, hr_data):
    """
    Validates firefighter data against HR data.
    Returns a list of validated firefighter objects.
    """
    validated_ffighters = []
    for ff in ffighters:
        # Find corresponding HR record by Employee Number
        hr_record = next((hr for hr in hr_data if str(hr['Employee Number']).strip() == str(ff.idnum).strip()), None)
        
        if hr_record:
            # Example validation: Check Hire Date consistency
            hire_date = datetime.strptime(hr_record['Hire Date'], '%m/%d/%Y').date()
            if ff.hireDate != hire_date:
                logger.warning(f"Mismatch for {ff.name} (ID: {ff.idnum}): Hire Date mismatch. Overwriting with HR data.")
                ff.hireDate = hire_date
            
            # Leave hours consistency (assuming these fields exist in the HR record)
            hr_vacation_hours = hr_record.get('# of Vacation Leave Hours awarded', 0)
            hr_holiday_hours = hr_record.get('# of Holiday Leave Hours awarded', 0)
            hr_total_allowed_day_count = (hr_vacation_hours + hr_holiday_hours) / 24
            if ff.approved_days_count != hr_total_allowed_day_count:
                logger.warning(f"Mismatch for {ff.name} (ID: {ff.idnum}): Max Days Off mismatch (HR Confirmed: {hr_total_allowed_day_count}, Got: {ff.max_days_off}). Overwriting with HR data.")
                ff.max_days_off = hr_total_allowed_day_count
            
            # If all checks pass, add firefighter to validated list
            validated_ffighters.append(ff)
        else:
            logger.warning(f"No matching HR record found for {ff.name} (ID: {ff.idnum}). Available HR IDs: {[str(hr['Employee Number']).strip() for hr in hr_data]}")

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
    main('firefighter_data.csv', 2024)
