# firefighter.py
from datetime import datetime
import random

import vacation_selection.setup_logging as setup_logging
logger = setup_logging.setup_logging("classes.log")

class Pick:
    def __init__(self, date, type="Untyped", determination="Unaddressed", increments='AMPM'):
        self.date = date
        self.type = type
        self.determination = determination
        self.reason = None
        self.increments = self.process_increments(increments)

    def process_increments(self, shift_selection):
        increment_mapping = {
            "AM": [1, 0],
            "PM": [0, 1],
            "AMPM": [1, 1]
        }
        if shift_selection in increment_mapping:
            return increment_mapping[shift_selection]
        else:
            # Log or raise an error if an unexpected value is passed
            print(f"Warning: Unexpected shift selection '{shift_selection}', defaulting to 'AMPM'")
            return [1, 1]
    
    def increments_plain_text(self, increment):
        reverse_mapping = {
            (1, 0): "AM",
            (0, 1): "PM",
            (1, 1): "FULL"
        }
        increment_tuple = tuple(increment)  # Convert the list to a tuple
        if increment_tuple in reverse_mapping:
            return reverse_mapping[increment_tuple]
        return "ERROR"
        
    def __str__(self):
        ret = f"{self.date} ({self.increments_plain_text(self.increments)}) ({self.type:^10}) - {self.determination}"
        if self.reason:
            ret += f' ({self.reason})'
        return ret

class FFighter:
    def __init__(self, idnum, fname, lname, hireDate, rank, shift, picks):
        self.fname = fname
        self.lname = lname
        self.name = f"{lname}, {fname[0]}"
        self.idnum = idnum
        self.rank = rank
        self.shift = shift
        self.hireDate = hireDate
        self.dice = random.random()
        self.processed = []
        self.picks = picks
        self.max_days_off = self.calculate_max_days_off()
        self.approved_days_count = 0

# Helper Functions

    def calculate_max_days_off(self):
        years_of_service = (datetime.now().date() - self.hireDate).days // 365
        return 4 + 8 + min(years_of_service // 5, 20)

    def print_picks(self):
        return ", ".join([str(pick) for pick in self.picks])

    def __str__(self):
        return self.name
