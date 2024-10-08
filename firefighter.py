# firefighter.py
from datetime import datetime
import random

class Pick:
    def __init__(self, date, type="U", determination="Unaddressed"):
        self.date = date
        self.type = type
        self.determination = determination
        self.reason = None

    def __str__(self):
        ret = f"{self.date} ({self.type:^10}) - {self.determination}"
        if self.reason:
            ret += f' ({self.reason})'
        return ret

class FFighter:
    def __init__(self, fname, lname, hireDate, rank, shift, picks):
        self.fname = fname
        self.lname = lname
        self.name = f"{lname}, {fname[0]}"
        self.rank = rank
        self.shift = shift
        self.hireDate = hireDate
        self.dice = random.random()
        self.processed = []
        self.picks = picks
        self.max_days_off = self.calculate_max_days_off()

    def calculate_max_days_off(self):
        years_of_service = (datetime.now().date() - self.hireDate).days // 365
        if years_of_service < 1:
            return 7
        elif 1 <= years_of_service < 5:
            return 14
        elif 5 <= years_of_service < 10:
            return 21
        else:
            return 28

    def print_picks(self):
        return ", ".join([str(pick) for pick in self.picks])

    def __str__(self):
        return self.name
