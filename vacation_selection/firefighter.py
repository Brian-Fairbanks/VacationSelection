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

    def get_increments(self):
        return self.increments

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
    
    def increments_plain_text(self, increment = None):
        if increment == None: increment = self.increments
        reverse_mapping = {
            (1, 0): "AM",
            (0, 1): "PM",
            (1, 1): "FULL"
        }
        increment_tuple = tuple(increment)  # Convert the list to a tuple
        if increment_tuple in reverse_mapping:
            return reverse_mapping[increment_tuple]
        return "ERROR"
    
    # Json Read/Write
    def to_dict(self):
        """Converts the Pick object to a dictionary."""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'type': self.type,
            'determination': self.determination,
            'reason': self.reason,
            'increments': self.increments_plain_text(self.increments)
        }

    @classmethod
    def from_dict(cls, pick_dict):
        """Creates a Pick object from a dictionary."""
        date = datetime.strptime(pick_dict['date'], '%Y-%m-%d')
        increments = pick_dict.get('increments', 'AMPM')
        pick = cls(
            date=date,
            type=pick_dict.get('type', "Untyped"),
            determination=pick_dict.get('determination', "Unaddressed"),
            increments=increments
        )
        pick.reason = pick_dict.get('reason')
        return pick
    
    # Pick print
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
        self.current_pick = None  # A holding place for the pick being processed

    def process_next_pick(self):
        """Move the next pick from the queue to the holding spot for approval or denial."""
        if self.picks:
            self.current_pick = self.picks.pop(0)
        else:
            self.current_pick = None

    def approve_current_pick(self):
        """Approve the current pick and update the firefighter's data."""
        if self.current_pick:
            self.current_pick.determination = "Approved"
            self.processed.append(self.current_pick)
            self.approved_days_count += sum(self.current_pick.increments) * (1 / len(self.current_pick.increments))
            self.current_pick = None

    def deny_current_pick(self, reason):
        """Deny the current pick with a reason and update the firefighter's data."""
        if self.current_pick:
            self.current_pick.determination = "Rejected"
            self.current_pick.reason = reason
            self.processed.append(self.current_pick)
            self.current_pick = None

    def calculate_max_days_off(self):
        years_of_service = (datetime.now().date() - self.hireDate).days // 365
        return 4 + 8 + min(years_of_service // 5, 20)

    def print_picks(self):
        return ", ".join([str(pick) for pick in self.picks])
    
    # Json Read/Write
    @classmethod
    def from_dict(cls, ff_dict):
        """Creates an FFighter object from a dictionary."""
        hireDate = datetime.strptime(ff_dict['hireDate'], '%Y-%m-%d')
        picks = [Pick.from_dict(pick) for pick in ff_dict.get('picks', [])]
        ffighter = cls(
            idnum=ff_dict.get('idnum', 0),
            fname=ff_dict.get('fname', ''),
            lname=ff_dict.get('lname', ''),
            hireDate=hireDate,
            rank=ff_dict.get('rank', ''),
            shift=ff_dict.get('shift', ''),
            picks=picks
        )
        ffighter.approved_days_count = ff_dict.get('approved_days_count', 0)
        ffighter.processed = [Pick.from_dict(proc) for proc in ff_dict.get('processed', [])]
        return ffighter

    def to_dict(self):
        """Converts the FFighter object to a dictionary."""
        return {
            'idnum': self.idnum,
            'fname': self.fname,
            'lname': self.lname,
            'name': self.name,
            'rank': self.rank,
            'shift': self.shift,
            'hireDate': self.hireDate.strftime('%Y-%m-%d'),
            'approved_days_count': self.approved_days_count,
            'max_days_off': self.max_days_off,
            'picks': [pick.to_dict() for pick in self.picks],
            'processed': [pick.to_dict() for pick in self.processed]
        }

    def __str__(self):
        return self.name
