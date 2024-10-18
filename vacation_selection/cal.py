from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')

import random


# Pick Validation Helpers
# ================================================================================================

def probationary_limitations(ffighter, calendar, rejected):
    """Checks if probationary ffighters are restricted from taking the day off."""

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


def has_reached_max_days(ffighter, calendar, rejected):
    """Checks if the ffighter has reached their maximum allowed days off."""
    if ffighter.approved_days_count >= ffighter.max_days_off:
        deny_ffighter_pick(ffighter, rejected, "Max days off already reached")
        return True
    return False


def day_has_available_slots(ffighter, calendar, rejected):
    """Checks if the requested increments (AM/PM) have available slots left."""
    date = ffighter.current_pick.date
    increments = ffighter.current_pick.increments

    # Ensure calendar for this date is initialized correctly
    if date not in calendar:
        calendar[date] = [[], []]  # Default to empty lists for AM and PM slots

    # Iterate over requested increments (AM or PM)
    for i, increment in enumerate(increments):
        if increment == 1:
            # Check if there are fewer than 5 slots filled for the requested increment (AM or PM)
            if len(calendar[date][i]) >= 5:
                deny_ffighter_pick(ffighter, rejected, f"Day already has 5 members off for {'AM' if i == 0 else 'PM'}")
                return False

    # If no issues found, return True indicating the requested increments are available
    return True


def ffighter_not_already_on_day(ffighter, calendar, rejected):
    """Checks if the ffighter is already approved for the requested day."""
    date = ffighter.current_pick.date

    # If the date is not in the calendar, ffighter has not requested the day
    if date not in calendar:
        return True

    # Loop over both increments (AM and PM)
    for increment_slots in calendar[date]:  # AM slots and PM slots
        # Loop over each slot to see if ffighter is already present
        for entry in increment_slots:
            if entry['ffighter'] == ffighter:
                deny_ffighter_pick(ffighter, rejected, "Already requested this day/time off")
                return False

    # If ffighter is not found in any of the increments, return True
    return True


def rank_limitation_checks(ffighter, calendar, rejected):
    """Checks if adding the ffighter would exceed the rank limitations for the day."""
    def count_rank_off(ranks):
        """Counts how many ffighters of the specified ranks are off on the given day."""
        total_count = 0

        # Iterate over both AM and PM slots in the calendar for the current date
        for increment_slots in calendar[ffighter.current_pick.date]:
            # Iterate over individual entries in each increment (AM/PM)
            for value in increment_slots:
                if value and value['ffighter'].rank in ranks:
                    total_count += 1

        return total_count

    # Specify current staffing counts and max allowed
    num_apparatus_specialists = count_rank_off(["Apparatus Specialist"])
    num_lieutenants = count_rank_off(["Lieutenant"])
    num_captains = count_rank_off(["Captain"])
    num_battalion_chiefs = count_rank_off(["Battalion Chief"])

    max_apparatus_specialists_off = 5
    max_lieutenants_off = 5 - num_captains
    max_captains_off = 3 - num_battalion_chiefs
    max_battalion_chiefs_off = min(2, 3 - num_captains)

    # Validate against rules for each rank
    if ffighter.rank == "Apparatus Specialist" and num_apparatus_specialists >= max_apparatus_specialists_off:
        deny_ffighter_pick(ffighter, rejected, f"Day already has {num_apparatus_specialists} Apparatus Specialists off")
        return False
    if ffighter.rank == "Lieutenant" and num_lieutenants >= max_lieutenants_off:
        deny_ffighter_pick(ffighter, rejected, f"Day already has {num_lieutenants} Lieutenants and {num_captains} Captains off")
        return False
    if ffighter.rank == "Captain" and num_captains >= max_captains_off:
        deny_ffighter_pick(ffighter, rejected, f"Day already has {num_captains} Captains, {num_lieutenants} Lieutenants, and {num_battalion_chiefs} Battalion Chiefs off")
        return False
    if ffighter.rank == "Battalion Chief" and num_battalion_chiefs >= max_battalion_chiefs_off:
        deny_ffighter_pick(ffighter, rejected, f"Day already has {num_battalion_chiefs} Battalion Chiefs and {num_captains} Captains off")
        return False

    return True


def process_pick_increments(ffighter, calendar):
    """Assigns the ffighter to the requested increments (AM/PM)."""
    date = ffighter.current_pick.date
    increments = ffighter.current_pick.increments

    # Ensure the calendar date is properly initialized as two empty lists for AM and PM
    if date not in calendar:
        calendar[date] = [[], []]  # Default to empty lists for AM and PM slots

    # Iterate over the requested increments (AM or PM)
    for i, increment in enumerate(increments):
        if increment == 1:
            # Only add the ffighter if there are available slots (less than 5)
            if len(calendar[date][i]) < 5:
                calendar[date][i].append({"ffighter": ffighter, "pick": ffighter.current_pick})
                ffighter.approve_current_pick()


def validate_pick_with_reasoning(ffighter, calendar, rejected):
    """Validates a pick, and assigns a reason if failure"""

    # Immediate Failures for probationary limitations and max days off
    if probationary_limitations(ffighter, calendar, rejected) or has_reached_max_days(ffighter, calendar, rejected):
        return False

    # Initialize the day in the calendar if not already present
    if ffighter.current_pick.date not in calendar:
        calendar[ffighter.current_pick.date] = [[], []]  # Default to AM and PM slots

    # Validate other conditions before proceeding with the pick
    if not (
        ffighter_not_already_on_day(ffighter, calendar, rejected)
        and day_has_available_slots(ffighter, calendar, rejected)
        and rank_limitation_checks(ffighter, calendar, rejected)
    ):
        return False

    # Send back OK to assign the date if all checks are passed
    process_pick_increments(ffighter, calendar)
    return True

def deny_ffighter_pick(ffighter, rejected, reason):
    """Denies the firefighter's current pick and adds it to the rejected list."""
    ffighter.deny_current_pick(reason)
    if ffighter.current_pick is None:  # After being denied, current_pick should be None
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
    # while a firefighter has valid picks remaining, keep trying until 2 are approved
    while dates_added < 2 and len(ffighter.picks) > 0:
        dates_added += process_ffighter_pick(ffighter, calendar, rejected)

def make_calendar(ffighters, silent_mode=False):
    """Analysis of ffighters picks: fully creates the calendar."""

    calendar = {}
    rejected = {}

    # until all firefighters have a determination for all picks...
    while any(filter(lambda x: len(x.picks), ffighters)):
        randomize_sub_priority(ffighters)
        if not silent_mode:
            logger.info("Processing a round of picks...")
        # grant no more than 2 picks per person per round
        for ffighter in ffighters:
            add_2_picks_for_ffighter(calendar, rejected, ffighter)

    return {"calendar": calendar, "rejected": rejected}
