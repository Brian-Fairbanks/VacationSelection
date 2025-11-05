from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')
from vacation_selection.increment import Increment

import random
from datetime import datetime

# Day Class
# ================================================================================================
class Day:
    # Class-level configurations for shift time structure
    # Configuration: Define increment names for the shift structure
    # For 24-hour shifts (1x24hr): ["FULL"]
    # For 24-hour shifts (2x12hr): ["AM", "PM"]
    # For 48-hour shifts (2x24hr): ["day_1", "day_2"]
    # For future 3-increment shifts: ["day_1", "day_2", "INCREMENT3"]
    increment_names = ["day_1", "day_2"]  # 48-hour shifts: 2x24hr segments
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

    def __init__(self, date):
        self.date = date
        self.ffighters = {}
        self.increments = {}
        self.rank_counts = {
            'Apparatus Specialist': 0,
            'Lieutenant': 0,
            'Captain': 0,
            'Battalion Chief': 0
        }
        # Create increments based on configuration
        if Day.is_single_increment():
            # Single increment mode (e.g., full 24-hour or 48-hour shift)
            self.increments = {0: Increment(date, Day.increment_names[0], only_increment=True)}
        else:
            # Multiple increment mode (e.g., AM/PM or day_1/day_2)
            self.increments = {i: Increment(date, name) for i, name in enumerate(Day.increment_names)}

    @staticmethod
    def get_header():
        # Header is the same regardless of increment configuration
        header = ['Date', 'First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth']
        return header
    
    def write_to_row(self, writer):
        for increment in self.increments.values():
            increment.write_to_row(writer)

    def __str__(self):
        # Build a list of increment strings in the same format as write_to_row
        increments_data = []
        for key, inc in self.increments.items():
            if inc.only_increment:
                # For only_increment, use both the firefighter name and idnum
                ffighters_str = ', '.join([
                    f"{ff.name} - {ff.idnum} ({pick.increments_plain_text()})"
                    for ff, pick in zip(inc.ffighters, inc.picks)
                ])
                inc_str = f"{inc.date}: {ffighters_str}"
            else:
                # Otherwise, include the increment name along with the firefighter names
                ffighters_str = ', '.join([
                    f"{ff.name} ({pick.increments_plain_text()})"
                    for ff, pick in zip(inc.ffighters, inc.picks)
                ])
                inc_str = f"{inc.date} ({inc.name}): {ffighters_str}"
            increments_data.append(inc_str)
        
        # Combine the day's date and all increment strings into one line.
        return f"{self.date}, " + " | ".join(increments_data)


    def _check_increments(self, ffighter, method_name, *args):
        """
        Helper function to iterate over increments and apply the given method.

        Args:
        increments: The list of increment values from the pick.
        method_name: The name of the method to call on each increment.
        *args: Additional arguments to pass to the method.

        Returns:
        True if the method returns True for any increment, False otherwise.
        """
        increments = ffighter.current_pick.increments

        if Day.is_single_increment():
            # Single increment mode - check the only increment
            increment = self.increments.get(0)
            if increment and getattr(increment, method_name)(*args):
                self.denial_reason = increment.denial_reason
                return True
        else:
            # Multiple increment mode - check each requested increment
            for inc_index, value in enumerate(increments):
                if value == 1:  # This increment is requested
                    increment = self.increments.get(inc_index)
                    if increment and getattr(increment, method_name)(*args):
                        self.denial_reason = increment.denial_reason
                        return True
        return False

    def is_full(self, ffighter):
        return self._check_increments(ffighter, "is_full")

    def is_rank_full(self, ffighter):
        return self._check_increments(ffighter, "is_rank_full", ffighter)

    def has_ffighter(self, ffighter):
        return self._check_increments(ffighter, "has_ffighter", ffighter)
    
    def can_add_ffighter(self, ffighter):
        if self.is_full(ffighter) or self.has_ffighter(ffighter) or self.is_rank_full(ffighter):
            return False
        return True
            
    def add_ffighter(self, ffighter):
        increments = ffighter.current_pick.get_increments()
        for inc_index, value in enumerate(increments):
            if value == 1:
                increment = self.increments.get(inc_index)
                if increment:
                    increment.add_ffighter(ffighter)
        return True


# Pick Validation Helpers
# ================================================================================================

def probationary_limitations(ffighter, rejected):
    """Checks if probationary firefighters are restricted from taking the day off."""

    days_since_hire = (ffighter.current_pick.date - ffighter.hireDate).days

    # No days allowed within the first 182 days
    if days_since_hire < 182:
        deny_ffighter_pick(ffighter, rejected, "No days off allowed within the first 182 days of hire")
        return True

    # Between 182 and 365 days: Only holidays are allowed, up to 4 days
    elif 182 <= days_since_hire < 365:
        approved_in_period = sum(
            1 for pick in ffighter.processed
            if 182 <= (pick.date - ffighter.hireDate).days < 365
            and pick.determination == "Approved"
        )
        if approved_in_period >= 4:
            deny_ffighter_pick(ffighter, rejected, "Reached 4 holidays limit between 182 and 365 days")
            return True
        ffighter.current_pick.type = "Holiday"

    # After 365 days, no probationary restrictions apply
    return False

def is_within_exclusion(ffighter, rejected):
    """
    Checks if the firefighter's current pick falls within an exclusion period.
    Handles both Pandas Timestamp and datetime.date types.
    """
    for exclusion in ffighter.exclusions:
        leave_start = exclusion.get('Leave Start')
        leave_end = exclusion.get('Leave End') or leave_start  # Default to Leave Start if Leave End is None

        # Convert to datetime.date if needed
        if hasattr(leave_start, 'date'):  # Pandas.Timestamp or datetime.datetime
            leave_start = leave_start.date()
        if hasattr(leave_end, 'date'):  # Pandas.Timestamp or datetime.datetime
            leave_end = leave_end.date()

        # Compare with the firefighter's pick date
        # print(f"{leave_start}({type(leave_start)}) <= {ffighter.current_pick.date}({type(ffighter.current_pick.date)}) <= {leave_end}({type(leave_end)})")
        if leave_start <= ffighter.current_pick.date <= leave_end:
            reason = f"Schedule Reassignment: ({exclusion.get('Reason', 'No reason provided')})"
            deny_ffighter_pick(ffighter, rejected, reason)
            return True
    return False


def has_reached_max_shifts(ffighter, rejected):
    """Checks if the firefighter has reached or would exceed their maximum allowed shifts off, considering fractional shifts."""
    # Calculate the requested shifts for the current pick
    increments = ffighter.current_pick.get_increments()  # Tuple like (1, 0), (1, 1), etc.
    increment_sum = sum(increments)  # Number of increments requested (e.g., 1 for half-shift, 2 for full-shift)

    # Determine fractional shifts requested
    fractional_shifts_requested = increment_sum * (1 / len(increments))
    
    # Calculate the new total shifts if the current pick is approved
    new_total_shifts = ffighter.approved_shifts_count + fractional_shifts_requested
    
    # Check if the firefighter has reached the max shifts off exactly
    if ffighter.approved_shifts_count == ffighter.max_shifts_off:
        deny_ffighter_pick(ffighter, rejected, "Max shifts off already reached")
        return True
    
    # Check if the new total would exceed the max shifts off
    if new_total_shifts > ffighter.max_shifts_off:
        deny_ffighter_pick(ffighter, rejected, "Shift would result in overage of time off")
        return True

    return False



def validate_pick_with_reasoning(ffighter, calendar, rejected, bypass_movement=False):

    # Immediate Failures for probationary limitations, max shifts off, and exclusions
    if not bypass_movement and(
        probationary_limitations(ffighter, rejected) or 
        has_reached_max_shifts(ffighter, rejected) or
        is_within_exclusion(ffighter, rejected)
    ):
        return False
    
    date = ffighter.current_pick.date
    if date not in calendar:
        calendar[date] = Day(date)
    day = calendar[date]

    # Validate other conditions before proceeding with the pick
    if not day.can_add_ffighter(ffighter):
        reason = getattr(day, 'denial_reason', "Pick Rejected, but not sure why")
        if bypass_movement:
            return reason
        deny_ffighter_pick(ffighter, rejected, reason)
        return False

    # All checks passed, add firefighter to the day
    if day.add_ffighter(ffighter):
        if not bypass_movement:
            ffighter.approve_current_pick()
    return True


def deny_ffighter_pick(ffighter, rejected, reason):
    """Denies the firefighter's current pick and adds it to the rejected list."""
    ffighter.deny_current_pick(reason)
    rejected.setdefault(ffighter.name, []).append(ffighter.processed[-1].date)


def process_ffighter_pick(ffighter, calendar, rejected):
    """Processes a single pick for the ffighter."""
    ffighter.process_next_pick()

    if ffighter.current_pick is None:  # When a ffighter is out of picks
        return 0

    if validate_pick_with_reasoning(ffighter, calendar, rejected):
        return 1
    else:
        return 0

# Other Helpers
# ================================================================================================
def randomize_sub_priority(ffighters):
    """Randomizes the sub-priority of firefighters with matching hire dates."""
    for ffighter in ffighters:
        ffighter.dice = random.random()
    ffighters.sort(key=lambda x: (x.hireDate, x.dice))

def printPriority(arr):
    logger.info(f"\n---=== Priority List at {datetime.now()} ===---\n")
    for ffighter in arr:
        logger.info(
            f'{ffighter.name:<20} : {str(ffighter.hireDate) :<10} - {ffighter.dice:< 22} :: [{ffighter.print_picks()}]')

# Calendar Formation
# ================================================================================================

def add_2_picks_for_ffighter(calendar, rejected, ffighter, count=2):
    """Attempts to add up to 2 picks for the firefighter."""
    dates_added = 0
    # While a firefighter has valid picks remaining, keep trying until 2 are approved
    while dates_added < count and len(ffighter.picks) > 0:
        dates_added += process_ffighter_pick(ffighter, calendar, rejected)

def make_calendar(ffighters, existing_calendar_data=None, rejected=None, silent_mode=False, count=2):
    """Analyzes firefighters' picks and fully creates the calendar."""
    if existing_calendar_data is None:
        calendar = {}
        rejected = {}
    else:
        # Extract the two dictionaries from the passed-in dictionary.
        calendar = existing_calendar_data.get("calendar", {})
        rejected = existing_calendar_data.get("rejected", {})
    
    # Until all firefighters have a determination for all picks...
    while any(filter(lambda x: len(x.picks), ffighters)):
        randomize_sub_priority(ffighters)
        if not silent_mode:
            printPriority(ffighters)
        # Grant no more than 2 picks per person per round
        for ffighter in ffighters:
            add_2_picks_for_ffighter(calendar, rejected, ffighter, count=2)
    
    return {"calendar": calendar, "rejected": rejected}

def recreate_calendar_from_json(ffighters):
    """Rebuilds the calendar structure while maintaining firefighter pick order.
       Uses validate_pick_with_reasoning to check each pick and prints a reason for any failure.
    """
    calendar = {}
    rejected = {}

    # Sort all processed picks by date > place > firefighter name
    sorted_picks = sorted(
        [pick for ff in ffighters for pick in ff.processed if pick.determination == "Approved"],
        key=lambda p: (p.date, p.place if p.place is not None else float('inf'), p.type)
    )

    for pick in sorted_picks:
        date = pick.date

        # Find the firefighter who made this pick
        ffighter = next((ff for ff in ffighters if pick in ff.processed), None)
        if not ffighter:
            day_info = calendar.get(date, "Day not created")
            logger.warning(
                f"Could not find firefighter for pick on {date}\n"
                f"Current day info: {day_info}\n"
                f"Pick info: {pick}\n"
            )
            continue

        # Set current pick for tracking
        ffighter.current_pick = pick

        # Validate the pick using the reasoning function.
        # bypass_movement=True makes the function return the denial reason (as a string)
        # instead of denying the pick.
        result = validate_pick_with_reasoning(ffighter, calendar, rejected, bypass_movement=True)
        if result is True:
            # If approved, assign the pick to the day's increments.
            day = calendar[date]
            increment = day.increments[0]  # Assuming a single-increment structure
            if pick.place is not None:
                # Place the pick at the given index, extending the list if necessary.
                while len(increment.picks) <= pick.place:
                    increment.picks.append(None)
                increment.picks[pick.place] = ffighter.current_pick
            else:
                increment.picks.append(ffighter.current_pick)
            # logger.info(f"Added {ffighter.name} to {date}: {result}\n")
        else:
            day_info = calendar.get(date, "Day not created")
            logger.warning(
                f"Could not reassign {ffighter.name} to {date}: {result}\n"
                f"{ffighter}\n"
                f"Current day info: {day_info}\n"
                f"Pick info: {pick}\n"
            )

    return {"calendar": calendar, "rejected": rejected}
