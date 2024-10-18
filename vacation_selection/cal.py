from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')

import random

# Day Class
# ================================================================================================
class Day:
    # Class-level configurations
    max_total_ffighters_allowed = 5
    max_apparatus_specialists_allowed = 5
    max_lieutenants_allowed = 5
    max_captains_allowed = 3
    max_battalion_chiefs_allowed = 2

    def __init__(self, date):
        self.date = date
        self.ffighters = []
        self.rank_counts = {
            'Probationary Firefighter':0,
            'Firefighter': 0,
            'Apparatus Specialist': 0,
            'Lieutenant': 0,
            'Captain': 0,
            'Battalion Chief': 0
        }
        self.increments = {'AM': [], 'PM': []}  # New attribute to store increments

    def is_full(self):
        return len(self.ffighters) >= Day.max_total_ffighters_allowed

    def can_add_rank(self, rank):
        rank_key = f'max_{rank.lower().replace(" ", "_")}s_allowed'
        max_allowed = getattr(Day, rank_key, None)
        if max_allowed is None:
            # If the rank is not specified, allow by default
            return True
        return self.rank_counts[rank] < max_allowed

    def has_ffighter(self, ffighter):
        return ffighter in self.ffighters

    def add_ffighter(self, ffighter):
        self.ffighters.append(ffighter)
        self.rank_counts[ffighter.rank] += 1

        # Store increment information
        increments = ffighter.current_pick.increments  # Assuming increments is a list like [1, 0] for AM only
        if increments[0] == 1:
            self.increments['AM'].append(ffighter)
        if increments[1] == 1:
            self.increments['PM'].append(ffighter)

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


def has_reached_max_days(ffighter, rejected):
    """Checks if the firefighter has reached their maximum allowed days off."""
    if ffighter.approved_days_count >= ffighter.max_days_off:
        deny_ffighter_pick(ffighter, rejected, "Max days off already reached")
        return True
    return False


def day_has_available_slots(ffighter, calendar, rejected):
    """Checks if the day has available slots."""
    date = ffighter.current_pick.date
    day = calendar.get(date)

    if day and day.is_full():
        deny_ffighter_pick(ffighter, rejected, "Day already has maximum firefighters off")
        return False

    return True


def ffighter_not_already_on_day(ffighter, calendar, rejected):
    """Checks if the firefighter is already approved for the requested day."""
    date = ffighter.current_pick.date
    day = calendar.get(date)

    if day and day.has_ffighter(ffighter):
        deny_ffighter_pick(ffighter, rejected, "Already requested this day off")
        return False

    return True
def rank_limitation_checks(ffighter, calendar, rejected):
    """Checks if adding the firefighter would exceed the rank limitations for the day."""
    date = ffighter.current_pick.date
    day = calendar.get(date)

    if not day:
        # If the day doesn't exist yet, it can't have rank limitations exceeded
        return True

    if not day.can_add_rank(ffighter.rank):
        deny_ffighter_pick(ffighter, rejected, f"Rank limitation reached for {ffighter.rank}")
        return False

    return True


def process_pick_increments(ffighter, calendar):
    """Assigns the firefighter to the requested increments (AM/PM)."""
    date = ffighter.current_pick.date
    if date not in calendar:
        calendar[date] = Day(date)
    day = calendar[date]

    if day.add_ffighter(ffighter):
        ffighter.approve_current_pick()

def validate_pick_with_reasoning(ffighter, calendar, rejected):
    """Validates a pick, and assigns a reason if failure"""

    # Immediate Failures for probationary limitations and max days off
    if probationary_limitations(ffighter, rejected) or has_reached_max_days(ffighter, rejected):
        return False

    # Validate other conditions before proceeding with the pick
    if not (
        ffighter_not_already_on_day(ffighter, calendar, rejected)
        and day_has_available_slots(ffighter, calendar, rejected)
        and rank_limitation_checks(ffighter, calendar, rejected)
    ):
        return False

    # All checks passed, add firefighter to the day
    process_pick_increments(ffighter, calendar)
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
            logger.info("Processing a round of picks...")
        # Grant no more than 2 picks per person per round
        for ffighter in ffighters:
            add_2_picks_for_ffighter(calendar, rejected, ffighter)

    return {"calendar": calendar, "rejected": rejected}
