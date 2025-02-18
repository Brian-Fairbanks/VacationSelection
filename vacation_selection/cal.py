from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')
from vacation_selection.increment import Increment

import random
from datetime import datetime

# Day Class
# ================================================================================================
class Day:
    # Class-level configurations remain the same...
    single_day_increment = True
    if single_day_increment:
        max_total_ffighters_allowed = 5
    else:
        max_total_ffighters_allowed = 10

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
        if self.single_day_increment:
            self.increments = {0: Increment(date, 'FULL', only_increment=True)}
        else:
            self.increments = {0: Increment(date, 'AM'), 1:Increment(date, 'PM')}

    @staticmethod
    def get_header():
        if Day.single_day_increment:
            header = ['Date', 'First', 'Second', 'Third', 'Fourth', 'Fifth']
        else:
            header = ['Date', 'First', 'Second', 'Third', 'Fourth', 'Fifth']
        return header
    
    def write_to_row(self, writer):
        for increment in self.increments.values():
            increment.write_to_row(writer)


    def _check_increments(self, ffighter, method_name, *args):
        """
        Helper function to iterate over increments and apply the given method.

        Args:
        increments: The list of increment values.
        method_name: The name of the method to call on each increment.
        *args: Additional arguments to pass to the method.

        Returns:
        True if the method returns True for any increment, False otherwise.
        """
        increments = ffighter.current_pick.increments

        if self.single_day_increment:
            increment = self.increments.get(0)
            if increment and getattr(increment, method_name)(*args):
                self.denial_reason = increment.denial_reason
                return True
        else:
            for inc_index, value in enumerate(increments):
                if value == 1:
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
        if leave_start <= ffighter.current_pick.date <= leave_end:
            reason = f"Schedule Reassignment: ({exclusion.get('Reason', 'No reason provided')})"
            deny_ffighter_pick(ffighter, rejected, reason)
            return True
    return False


def has_reached_max_days(ffighter, rejected):
    """Checks if the firefighter has reached or would exceed their maximum allowed days off, considering fractional days."""
    
    # Calculate the requested days for the current pick
    increments = ffighter.current_pick.get_increments()  # Tuple like (1, 0), (1, 1), etc.
    increment_sum = sum(increments)  # Number of increments requested (e.g., 1 for half-day, 2 for full-day)
    
    # Determine fractional days requested
    fractional_days_requested = increment_sum * (1 / len(increments))
    
    # Calculate the new total days if the current pick is approved
    new_total_days = ffighter.approved_days_count + fractional_days_requested
    
    # Check if the firefighter has reached the max days off exactly
    if ffighter.approved_days_count == ffighter.max_days_off:
        deny_ffighter_pick(ffighter, rejected, "Max days off already reached")
        return True
    
    # Check if the new total would exceed the max days off
    if new_total_days > ffighter.max_days_off:
        deny_ffighter_pick(ffighter, rejected, "Day would result in overage of time off")
        return True

    return False



def validate_pick_with_reasoning(ffighter, calendar, rejected):

    # Immediate Failures for probationary limitations, max days off, and exclusions
    if (
        probationary_limitations(ffighter, rejected) or 
        has_reached_max_days(ffighter, rejected) or
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
        deny_ffighter_pick(ffighter, rejected, reason)
        return False

    # All checks passed, add firefighter to the day
    if day.add_ffighter(ffighter):
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

def add_2_picks_for_ffighter(calendar, rejected, ffighter):
    """Attempts to add up to 2 picks for the firefighter."""
    dates_added = 0
    # While a firefighter has valid picks remaining, keep trying until 2 are approved
    while dates_added < 2 and len(ffighter.picks) > 0:
        dates_added += process_ffighter_pick(ffighter, calendar, rejected)

def make_calendar(ffighters, silent_mode=False):
    """Analyzes firefighters' picks and fully creates the calendar."""

    calendar = {}
    rejected = {}

    # Until all firefighters have a determination for all picks...
    while any(filter(lambda x: len(x.picks), ffighters)):
        randomize_sub_priority(ffighters)
        if not silent_mode:
            printPriority(ffighters)
        # Grant no more than 2 picks per person per round
        for ffighter in ffighters:
            add_2_picks_for_ffighter(calendar, rejected, ffighter)

    return {"calendar": calendar, "rejected": rejected}

def recreate_calendar_from_json(ffighters):
    """Rebuilds the calendar structure from JSON firefighter data."""
    calendar = {}
    rejected = {}

    for ffighter in ffighters:
        for pick in ffighter.processed:
            if pick.determination == "Approved":
                date = pick.date

                # Create day if it doesn't exist
                if date not in calendar:
                    calendar[date] = Day(date)

                day = calendar[date]

                # Set the current pick for proper increment tracking
                ffighter.current_pick = pick

                # Assign firefighter to the day
                if day.can_add_ffighter(ffighter):
                    day.add_ffighter(ffighter)
                else:
                    logger.warning(f"Could not reassign {ffighter.name} to {date}, possibly due to rank or count limits.")

    return {"calendar": calendar, "rejected": rejected}  # ✅ Ensure this matches make_calendar()