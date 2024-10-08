# main.py
from datetime import datetime
from file_io import read_firefighter_data, write_calendar_to_csv
from firefighter import FFighter
from priority import set_priorities, randomize_sub_priority
from cal import make_calendar
from logger import setup_logging

def main():
    runtime = datetime.now().strftime("%Y.%m.%d %H.%M")
    write_path = "./output"
    logger = setup_logging(write_path, runtime)
    date_format = '%m-%d-%Y'

    try:
        print("Opening Fire")
        file = read_firefighter_data('.//Old Files//2024 VACATION REQUEST FORM - Form Responses.csv', date_format)
        print("worked!")
        ffighters = set_priorities(file)
    except Exception as e:
        print(e)

    print(ffighters)

    for shift in ["A", "B", "C"]:
        shift_members = [ff for ff in ffighters if ff.shift == shift]
        results = make_calendar(shift_members)
        write_calendar_to_csv(results['calendar'], shift, write_path, runtime)

if __name__ == '__main__':
    main()