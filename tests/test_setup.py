# tests/test_setup.py
import os
from vacation_selection.file_io import read_firefighter_data
from vacation_selection.priority import set_priorities
from vacation_selection.cal import make_calendar

# Set global variables for testing paths and formats
TEST_DIR = './2025 Test CSVs'
DATE_FORMAT = '%m-%d-%Y'

def run_calendar_for_file(filename, shift='A', silent_mode=True):
    """
    Helper function to read, prioritize, and make a calendar for a given file.
    
    Args:
        filename (str): Name of the test file.
        shift (str): The shift to filter for ('A', 'B', 'C').
        silent_mode (bool): If True, suppresses logging output from make_calendar.

    Returns:
        tuple: The calendar results and shift members.
    """
    file_path = os.path.join(TEST_DIR, filename)
    ffighters = read_firefighter_data(file_path, DATE_FORMAT, 2025)
    ffighters = set_priorities(ffighters)

    shift_members = [ff for ff in ffighters if ff.shift == shift]
    results = make_calendar(shift_members, silent_mode)

    return results, shift_members
