# increment.py
from vacation_selection.setup_logging import setup_logging
logger = setup_logging('Increment')
from datetime import date, timedelta

# Increment Class
# ================================================================================================
class Increment:
    # Class-level configurations remain the same...
    max_total_ffighters_allowed = 6

    def __init__(self, date, name, only_increment=False ):
        self.date = date
        self.is_holiday = check_holiday(date)
        self.name = name
        self.only_increment = only_increment
        self.ffighters = []
        self.picks=[]
        self.rank_counts = {
            'Apparatus Specialist': 0,
            'Lieutenant': 0,
            'Captain': 0,
            'Battalion Chief': 0
        }
        self.denial_reason=""

    def format_date_display(self):
        """
        Format the date for display based on shift duration.
        For 48-hour shifts starting Feb 4, 2025, shows date range (e.g., "Oct 28-29").
        For 24-hour shifts, shows single date.
        """
        from vacation_selection.cal import Day

        # Check if this is after the transition date and using 48-hour shifts
        if (Day.shift_duration_hours == 48 and
            hasattr(Day, 'transition_date') and
            self.date >= Day.transition_date):
            # Calculate end date (48 hours = 2 days)
            end_date = self.date + timedelta(days=1)

            # Format as "Oct 28-29" or "Dec 31-Jan 1" for month transitions
            if self.date.month == end_date.month:
                return f"{self.date.strftime('%b %d')}-{end_date.day}"
            else:
                return f"{self.date.strftime('%b %d')}-{end_date.strftime('%b %d')}"
        else:
            # 24-hour shift or before transition - show single date
            return self.date.strftime('%Y-%m-%d')

    def write_to_row(self, writer):
        """Write the increment details to the CSV row."""
        date_display = self.format_date_display()

        # Prepare the list of firefighters with increment details
        if self.only_increment:
            # Include only the firefighter names with increments_plain_text()
            all_ffighters = [f"{ff.name} - {ff.idnum} ({pick.increments_plain_text()})" for ff, pick in zip(self.ffighters, self.picks)]
            row = [date_display] + (all_ffighters + [""] * self.max_total_ffighters_allowed)[:self.max_total_ffighters_allowed]
        else:
            # Include firefighter names with increment names
            all_ffighters = [f"{ff.name} ({pick.increments_plain_text()})" for ff, pick in zip(self.ffighters, self.picks)]
            row = [f"{date_display} ({self.name})"] + (all_ffighters + [""] * self.max_total_ffighters_allowed)[:self.max_total_ffighters_allowed]

        writer.writerow(row)



    def is_full(self):
        isfull = len(self.ffighters) >= Increment.max_total_ffighters_allowed
        if isfull:
            self.denial_reason = "Day already has maximum firefighters off"
        return isfull
        

    def is_rank_full(self, ffighter):
        rank = ffighter.rank
        # Current counts
        num_apparatus_specialists = self.rank_counts['Apparatus Specialist']
        num_lieutenants = self.rank_counts['Lieutenant']
        num_captains = self.rank_counts['Captain']
        num_battalion_chiefs = self.rank_counts['Battalion Chief']

        # Calculate maximums
        max_firefighters_off = self.max_total_ffighters_allowed  # No dependencies
        max_apparatus_specialists_off = self.max_total_ffighters_allowed  # No dependencies
        max_lieutenants_off = 5 - num_captains
        max_captains_off = 3 - num_battalion_chiefs
        max_battalion_chiefs_off = min(2, 3 - num_captains)

        def failed_holiday_exception():
            if self.is_holiday and (num_captains > 0 or num_battalion_chiefs > 0) :
                self.denial_reason = f"Increment is a holiday, and already has {num_captains} Captains, and {num_battalion_chiefs} Battalion Chiefs off"
                return True
            return False

        # Check limitations
        if rank == 'Apparatus Specialist':
            if num_apparatus_specialists >= max_apparatus_specialists_off:
                self.denial_reason = f"Increment already has {num_apparatus_specialists} Apparatus Specialists off"
                return True
        elif rank == 'Lieutenant':
            if num_lieutenants >= max_lieutenants_off:
                self.denial_reason = f"Increment already has {num_lieutenants} Lieutenants and {num_captains} Captains off"
                return True
        elif rank == 'Captain':
            if failed_holiday_exception():
                return True               
            if num_captains >= max_captains_off:
                self.denial_reason = f"Increment already has {num_captains} Captains, {num_lieutenants} Lieutenants, and {num_battalion_chiefs} Battalion Chiefs off"
                return True
        elif rank == 'Battalion Chief':
            if failed_holiday_exception():
                return True
            if num_battalion_chiefs >= max_battalion_chiefs_off:
                self.denial_reason = f"Increment already has {num_battalion_chiefs} Battalion Chiefs and {num_captains} Captains off"
                return True

        # If no limitations are exceeded, allow addition
        return False


    def has_ffighter(self, ffighter):
        check = ffighter in self.ffighters
        if check:
            self.denial_reason = f"Already requested this day off ({self.name})"
            # logger.warning("FAILED ON ALREADY ASSIGNED")
        return check
    
    def add_ffighter(self, ffighter):
        increment = self  # The current increment object
        # Find the number of previously added firefighters
        place_index = len(increment.picks)
        # Assign place based on this position
        ffighter.current_pick.place = place_index
        
        self.ffighters.append(ffighter)
        # Update rank counts
        if ffighter.rank not in self.rank_counts:
            self.rank_counts[ffighter.rank] = 0
        self.rank_counts[ffighter.rank] += 1
        self.picks.append(ffighter.current_pick)
        return True


def check_holiday(day: date) -> bool:
    def nth_weekday(year, month, weekday, n):
        first_day = date(year, month, 1)
        offset = (weekday - first_day.weekday()) % 7
        return first_day + timedelta(days=offset + (n-1)*7)

    def last_monday(year, month):
        last_day = date(year, month + 1, 1) - timedelta(days=1)
        while last_day.weekday() != 0:  # Monday
            last_day -= timedelta(days=1)
        return last_day

    y, m, d = day.year, day.month, day.day

    fixed_holidays = [
        (1, 1),   # New Year's Day
        (6, 19),  # Juneteenth
        (7, 4),   # Independence Day
        (11, 11), # Veterans Day
        (12, 24), # Christmas Eve
        (12, 25), # Christmas Day
        # (12, 26)  # Boxing Day
    ]

    if (m, d) in fixed_holidays:
        return True

    variable_holidays = [
        nth_weekday(y, 1, 0, 3),  # MLK Day
        nth_weekday(y, 2, 0, 3),  # President's Day
        last_monday(y, 5),        # Memorial Day
        nth_weekday(y, 9, 0, 1),  # Labor Day
        nth_weekday(y, 11, 3, 4)  # Thanksgiving
    ]
    if day in variable_holidays:
        return True

    return False