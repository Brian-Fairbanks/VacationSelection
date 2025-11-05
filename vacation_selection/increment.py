# increment.py
from vacation_selection.setup_logging import setup_logging
logger = setup_logging('Increment')
from datetime import date, datetime, timedelta

# Increment Class
# ================================================================================================
class Increment:
    # Class-level configurations for increment structure
    # Configuration: Define increment names for the shift structure
    # For 24-hour shifts (1x24hr): ["FULL"]
    # For 24-hour shifts (2x12hr): ["AM", "PM"]
    # For 48-hour shifts (2x24hr): ["day_1", "day_2"]
    # For future 3-increment shifts: ["day_1", "day_2", "INCREMENT3"]
    increment_names = ["day_1", "day_2"]  # 48-hour shifts: 2x24hr segments

    # Maximum firefighters allowed per increment
    max_total_ffighters_allowed = 6

    # Shift duration configuration (in hours)
    # For 24-hour shifts: shift_duration_hours = 24
    # For 48-hour shifts: shift_duration_hours = 48
    shift_duration_hours = 48
    transition_date = datetime(2025, 2, 4).date()  # Date when 48-hour shifts begin

    @classmethod
    def is_single_increment(cls):
        """Returns True if only one increment is configured."""
        return len(cls.increment_names) == 1

    def __init__(self, date, name, only_increment=False ):
        self.date = date
        self.is_holiday = check_holiday(date)
        self.name = name
        self.only_increment = only_increment
        self.ffighters = []
        self.picks=[]
        self.runner_ups = []  # List of (ffighter, pick, reason) tuples for denied requests in order
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
        # Check if this is after the transition date and using 48-hour shifts
        if (Increment.shift_duration_hours == 48 and
            hasattr(Increment, 'transition_date') and
            self.date >= Increment.transition_date):
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

    def add_runner_up(self, ffighter, pick, reason):
        """
        Add a denied pick to the runner-up list for this increment.
        Runner-ups are stored in order of denial (which corresponds to seniority order).

        Args:
            ffighter: The firefighter whose pick was denied
            pick: The Pick object that was denied
            reason: The reason for denial
        """
        self.runner_ups.append({
            'ffighter': ffighter,
            'pick': pick,
            'reason': reason,
            'position': len(self.runner_ups) + 1  # 1-indexed position
        })

    @staticmethod
    def process_increments(shift_selection):
        """
        Process increment selection string into a list of increment flags.
        Supports both legacy (AM/PM) and new (day_1/day_2) naming.
        Can be extended to support 3+ increments.

        Args:
            shift_selection: String representing the increment selection (e.g., "day_1", "day_1day_2", "FULL")

        Returns:
            List of integers (0 or 1) representing which increments are selected

        Examples:
            >>> Increment.process_increments("day_1")
            [1, 0]
            >>> Increment.process_increments("day_1day_2")
            [1, 1]
            >>> Increment.process_increments("FULL")
            [1, 1]
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
            logger.warning(f"Unexpected shift selection '{shift_selection}', defaulting to 'FULL'")
            return [1, 1]

    @staticmethod
    def increments_to_plain_text(increment_list, increment_names=None):
        """
        Convert increment list back to plain text representation.

        Args:
            increment_list: List of integers (0 or 1) representing which increments are selected
            increment_names: Optional list of increment names. If None, uses Increment.increment_names

        Returns:
            String representation of the increment selection

        Examples:
            >>> Increment.increments_to_plain_text([1, 0], ["day_1", "day_2"])
            'day_1'
            >>> Increment.increments_to_plain_text([1, 1], ["day_1", "day_2"])
            'FULL'
            >>> Increment.increments_to_plain_text([1, 0, 1], ["day_1", "day_2", "day_3"])
            'day_1+day_3'
        """
        # Use Increment's own class variable if not provided
        if increment_names is None:
            increment_names = Increment.increment_names

        increment_tuple = tuple(increment_list)
        num_increments = len(increment_names)

        # Handle FULL (all increments selected)
        if all(v == 1 for v in increment_list):
            return "FULL"

        # Handle single increment selections
        for i, name in enumerate(increment_names):
            expected_pattern = [1 if j == i else 0 for j in range(num_increments)]
            if increment_tuple == tuple(expected_pattern):
                return name

        # Handle combinations (for display purposes)
        selected = [increment_names[i] for i, v in enumerate(increment_list) if v == 1]
        if selected:
            return "+".join(selected)

        return "ERROR"


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