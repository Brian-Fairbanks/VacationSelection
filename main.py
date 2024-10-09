# main.py
from datetime import datetime
from setup_logging import setup_logging

runtime = datetime.now().strftime("%Y.%m.%d %H.%M")
write_path = ".//output"
logger = setup_logging(f"RunLog-{runtime}.log", base=write_path, debug=False)
print = logger.info

from file_io import read_firefighter_data, write_calendar_to_csv, write_picks_to_csv, print_final
from firefighter import FFighter
from priority import set_priorities, randomize_sub_priority
from cal import make_calendar


def main():
    date_format = '%m-%d-%Y'

    # Import File
    try:
        file = read_firefighter_data('.//Old Files//2024 VACATION REQUEST FORM - Form Responses Final.csv', date_format, 2024)
        ffighters = set_priorities(file)
    except Exception as e:
        logger.error("ERROR: {e}")

    # Work in shifts:
    for shift in ["A", "B", "C"]:
        shift_members = [ff for ff in ffighters if ff.shift == shift]
        results = make_calendar(shift_members)
        write_calendar_to_csv(results['calendar'], shift, write_path, runtime)
        write_picks_to_csv(shift_members, shift, write_path, runtime)
        print_final(shift_members)

if __name__ == '__main__':
    main()