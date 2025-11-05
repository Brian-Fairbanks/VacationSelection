# firefighter.py
from datetime import datetime
import random

import vacation_selection.setup_logging as setup_logging
logger = setup_logging.setup_logging("classes.log")

class Pick:
    def __init__(self, date, type="Untyped", determination="Unaddressed", increments='AMPM', reason=None, place=None, source=None):
        self.date = date
        self.type = type
        self.determination = determination
        self.reason = reason
        self.increments = self.process_increments(increments)  # Requested increments
        self.approved_increments = None  # Will be set when pick is approved (can differ from requested)
        self.place = place
        self.source = source

    def get_increments(self):
        """Returns requested increments."""
        return self.increments

    def get_approved_increments(self):
        """Returns approved increments (or requested if not yet set)."""
        return self.approved_increments if self.approved_increments is not None else self.increments

    def process_increments(self, shift_selection):
        """
        Process increment selection string into a list of increment flags.
        Supports both legacy (AM/PM) and new (day_1/day_2) naming.
        Can be extended to support 3+ increments.
        """
        increment_mapping = {
            # Legacy 24-hour shift names (2x12hr segments)
            "AM": [1, 0],
            "PM": [0, 1],
            "AMPM": [1, 1],
            "FULL": [1, 1],
            # New 48-hour shift names (2x24hr segments)
            "day_1": [1, 0],
            "day_2": [0, 1],
            "day_1day_2": [1, 1],
            # Future 3-increment support
            "INCREMENT1": [1, 0, 0],
            "INCREMENT2": [0, 1, 0],
            "INCREMENT1INCREMENT2": [1, 1, 0],
            "INCREMENT3": [0, 0, 1],
            "INCREMENT1INCREMENT3": [1, 0, 1],
            "INCREMENT2INCREMENT3": [0, 1, 1],
            "INCREMENT1INCREMENT2INCREMENT3": [1, 1, 1],
        }
        if shift_selection in increment_mapping:
            return increment_mapping[shift_selection]
        else:
            # Log or raise an error if an unexpected value is passed
            print(f"Warning: Unexpected shift selection '{shift_selection}', defaulting to 'FULL'")
            return [1, 1]
        
    def increments_plain_text(self, increment = None):
        """
        Convert increment list back to plain text representation.
        Uses the current Day.increment_names configuration to determine naming.
        """
        if increment == None:
            increment = self.increments

        # Import here to avoid circular dependency
        from vacation_selection.cal import Day

        increment_tuple = tuple(increment)
        num_increments = len(Day.increment_names)

        # Handle FULL (all increments selected)
        if all(v == 1 for v in increment):
            return "FULL"

        # Handle single increment selections
        for i, name in enumerate(Day.increment_names):
            expected_pattern = [1 if j == i else 0 for j in range(num_increments)]
            if increment_tuple == tuple(expected_pattern):
                return name

        # Handle combinations (for display purposes)
        selected = [Day.increment_names[i] for i, v in enumerate(increment) if v == 1]
        if selected:
            return "+".join(selected)

        return "ERROR"
    
    # Json Read/Write
    def to_dict(self):
        """Converts the Pick object to a dictionary."""
        # For approved picks, show what was actually approved
        # For denied/unaddressed picks, show what was requested
        if self.determination == "Approved" and self.approved_increments is not None:
            increments_text = self.increments_plain_text(self.approved_increments)
        else:
            increments_text = self.increments_plain_text(self.increments)

        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'type': self.type,
            'determination': self.determination,
            'reason': self.reason,
            'increments': increments_text,
            "place": self.place,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, pick_dict):
        """Creates a Pick object from a dictionary."""
        date = datetime.strptime(pick_dict['date'], '%Y-%m-%d').date()  # Ensure date is converted properly
        increments = pick_dict.get('increments', [1, 1])  # Default to full day

        pick = cls(
            date=date,
            type=pick_dict.get('type', "Untyped"),
            determination=pick_dict.get('determination', "Unaddressed"),
            increments=increments,
            place=pick_dict.get('place'),  # Restores the order position
            source=pick_dict.get('source')
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
        self.hr_validations = None
        self.processed = []
        self.picks = picks
        self.exclusions = []

        # Calculate max shifts off and unpack the dictionary
        shifts_off_data = self.calculate_max_shifts_off()
        self.awarded_holiday_shifts = shifts_off_data['total_holiday_shifts']
        self.awarded_vacation_shifts = shifts_off_data['total_vacation_shifts']
        self.max_shifts_off = shifts_off_data['max_shifts_off']

        self.used_vacation_shifts = 0
        self.used_holiday_shifts = 0
        self.approved_shifts_count = 0
        self.current_pick = None  # A holding place for the pick being processed

    def process_next_pick(self):
        """Move the next pick from the queue to the holding spot for approval or denial."""
        if self.picks:
            self.current_pick = self.picks.pop(0)
        else:
            self.current_pick = None

    def approve_current_pick(self, reason=None):
        """
        Approve the current pick and update the firefighter's data.
        If reason is provided, it will be set (e.g., for partial grants).
        """
        if self.current_pick:
            self.current_pick.determination = "Approved"

            # Set reason if provided (e.g., "Partial grant - only day_1 available")
            if reason:
                self.current_pick.reason = reason

            # Use approved_increments (which may differ from requested for partial grants)
            approved_increments = self.current_pick.get_approved_increments()
            approved_hours = sum(approved_increments) * (1 / len(approved_increments))

            if self.used_vacation_shifts + approved_hours <= self.awarded_vacation_shifts:
                self.used_vacation_shifts += approved_hours
                self.current_pick.type = "Vacation"
            else:
                self.used_holiday_shifts += approved_hours
                self.current_pick.type = "Holiday"
            self.processed.append(self.current_pick)
            self.approved_shifts_count += approved_hours
            self.current_pick = None

    def deny_current_pick(self, reason):
        """Deny the current pick with a reason and update the firefighter's data."""
        if self.current_pick:
            self.current_pick.determination = "Rejected"
            self.current_pick.reason = reason
            self.processed.append(self.current_pick)
            self.current_pick = None

    def calculate_max_shifts_off(self):
        # Calculate years of service rounded to the nearest full year
        years_of_service = (datetime.now().date() - self.hireDate).days // 365

        # Base and additional shifts calculation
        base_vacation_shifts = 8  # Base vacation shifts
        base_holiday_shifts = 6   # Base holiday shifts
        additional_shifts = min(years_of_service // 5, 6)  # Additional shifts based on years of service, capped at 20 total shifts

        # Total allowed shifts off
        max_shifts_off = base_vacation_shifts + additional_shifts + base_holiday_shifts

        # Return the breakdown of shifts in a dictionary
        return {
            'total_holiday_shifts': base_holiday_shifts,
            'total_vacation_shifts': base_vacation_shifts + additional_shifts,
            'max_shifts_off': max_shifts_off
        }

    def print_picks(self):
        return ", ".join([str(pick) for pick in self.picks])
    
    # Add exclusion
    def add_exclusion(self, leave_start, leave_end=None, reason=None):
        exclusion = {
            "Leave Start": leave_start,
            "Leave End": leave_end,
            "Reason": reason
        }
        self.exclusions.append(exclusion)

    
    # Json Read/Write
    @classmethod
    def from_dict(cls, ff_dict):
        hire_date = datetime.strptime(ff_dict['hireDate'], '%Y-%m-%d').date()
        ff = cls(
            idnum=ff_dict.get('idnum', 0),
            fname=ff_dict.get('fname', ''),
            lname=ff_dict.get('lname', ''),
            hireDate=hire_date,
            rank=ff_dict.get('rank', ''),
            shift=ff_dict.get('shift', ''),
            picks=[Pick.from_dict(pick) for pick in ff_dict.get('picks', [])]
        )
        ff.exclusions = ff_dict.get('exclusions', [])  # Load exclusions
        ff.max_shifts_off = ff_dict.get('max_shifts_off', 0)
        ff.awarded_vacation_shifts = ff_dict.get('awarded_vacation_shifts', 0)
        ff.awarded_holiday_shifts = ff_dict.get('awarded_holiday_shifts', 0)
        ff.used_vacation_shifts = ff_dict.get('used_vacation_shifts', 0)
        ff.used_holiday_shifts = ff_dict.get('used_holiday_shifts', 0)
        ff.approved_shifts_count = ff_dict.get('approved_shifts_count', 0)
        ff.processed = [Pick.from_dict(proc) for proc in ff_dict.get('processed', [])]
        ff.hr_validations = ff_dict.get('hr_validations', {})
        return ff


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
            'max_shifts_off': self.max_shifts_off,
            'awarded_vacation_shifts': self.awarded_vacation_shifts,
            'awarded_holiday_shifts': self.awarded_holiday_shifts,
            'used_vacation_shifts': self.used_vacation_shifts,
            'used_holiday_shifts': self.used_holiday_shifts,
            'approved_shifts_count': self.approved_shifts_count,
            'picks': [pick.to_dict() for pick in self.picks],
            'processed': [pick.to_dict() for pick in self.processed],
            'hr_validations': self.hr_validations,
            'exclusions': self.exclusions
        }

    def __str__(self):
        return self.name
