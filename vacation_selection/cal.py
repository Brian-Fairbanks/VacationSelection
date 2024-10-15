from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')

import random


# Pick Validation Helpers
# =================================================================================================

def probationary_limitations(ffighter, current_pick):
    """Checks if probationary firefighters are restricted from taking the day off."""

    days_since_hire = (current_pick.date - ffighter.hireDate).days

    # No days allowed within the first 182 days
    if days_since_hire < 182:
        current_pick.reason = "No days off allowed within the first 182 days of hire"
        return True

    # Between 182 and 365 days: Only holidays are allowed, up to 4 days
    elif 182 <= days_since_hire < 365:
        approved_in_period = sum(
            1 for pick in ffighter.processed
            if 182 <= (pick.date - ffighter.hireDate).days < 365
            and pick.determination == "Approved"
        )
        if approved_in_period >= 4:
            current_pick.reason = "Reached 4 holidays limit between 182 and 365 days"
            return True
        current_pick.type = "Holiday"

    # After 365 days, no probationary restrictions apply
    return False


def has_reached_max_days(ffighter, current_pick):
    """Checks if the firefighter has reached their maximum allowed days off."""
    if ffighter.approved_days_count >= ffighter.max_days_off:
        current_pick.reason = "Max days off already reached"
        return True
    return False

def day_has_available_slots(calendar, current_pick):
    """Checks if the requested increments (AM/PM) have available slots left."""
    date = current_pick.date
    increments = current_pick.increments

    # Ensure calendar for this date is initialized correctly
    if date not in calendar:
        calendar[date] = [[], []]  # Default to empty lists for AM and PM slots

    # Iterate over requested increments (AM or PM)
    for i, increment in enumerate(increments):
        if increment == 1:
            # Check if there are fewer than 5 slots filled for the requested increment (AM or PM)
            if len(calendar[date][i]) >= 5:
                current_pick.reason = f"Day already has 5 members off for {'AM' if i == 0 else 'PM'}"
                return False

    # If no issues found, return True indicating the requested increments are available
    return True

def ffighter_not_already_on_day(calendar, ffighter, current_pick):
    """Checks if the firefighter is already approved for the requested day."""
    date = current_pick.date

    # If the date is not in the calendar, firefighter has not requested the day
    if date not in calendar:
        return True

    # Loop over both increments (AM and PM)
    for increment_slots in calendar[date]:  # AM slots and PM slots
        # Loop over each slot to see if firefighter is already present
        for entry in increment_slots:
            if entry['ffighter'] == ffighter:
                current_pick.reason = "Already requested this day/time off"
                return False

    # If firefighter is not found in any of the increments, return True
    return True


def rank_limitation_checks(calendar, ffighter, current_pick):
    """Checks if adding the firefighter would exceed the rank limitations for the day."""
    def count_rank_off(ranks):
        """Counts how many firefighters of the specified ranks are off on the given day."""
        total_count = 0

        # Iterate over both AM and PM slots in the calendar for the current date
        for increment_slots in calendar[current_pick.date]:
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
        current_pick.reason = f"Day already has {num_apparatus_specialists} Apparatus Specialists off"
        return False
    if ffighter.rank == "Lieutenant" and num_lieutenants >= max_lieutenants_off:
        current_pick.reason = f"Day already has {num_lieutenants} Lieutenants and {num_captains} Captains off"
        return False
    if ffighter.rank == "Captain" and num_captains >= max_captains_off:
        current_pick.reason = f"Day already has {num_captains} Captains, {num_lieutenants} Lieutenants, and {num_battalion_chiefs} Battalion Chiefs off"
        return False
    if ffighter.rank == "Battalion Chief" and num_battalion_chiefs >= max_battalion_chiefs_off:
        current_pick.reason = f"Day already has {num_battalion_chiefs} Battalion Chiefs and {num_captains} Captains off"
        return False

    return True

def process_pick_increments(calendar, ffighter, current_pick):
    """Assigns the firefighter to the requested increments (AM/PM)."""
    date = current_pick.date
    increments = current_pick.increments

    # Ensure the calendar date is properly initialized as two empty lists for AM and PM
    if date not in calendar:
        calendar[date] = [[], []]  # Default to empty lists for AM and PM slots

    # Iterate over the requested increments (AM or PM)
    for i, increment in enumerate(increments):
        if increment == 1:
            # Only add the firefighter if there are available slots (less than 5)
            if len(calendar[date][i]) < 5:
                calendar[date][i].append({"ffighter": ffighter, "pick": current_pick})
                ffighter.approved_days_count += 0.5



# Pick Assignment
# =================================================================================================

def validate_pick_with_reasoning(calendar, ffighter, current_pick):
    """validates a pick, and assigns a reason if failure"""

    # Immediate Failures for probationary limitations and max days off
    if probationary_limitations(ffighter, current_pick) or has_reached_max_days(ffighter, current_pick):
        return False

    # Initialize the day in the calendar if not already present
    if current_pick.date not in calendar:
        calendar[current_pick.date] = [[],[]]  # Default to AM and PM slots

    # Validate other conditions before proceeding with the pick
    if not (
        day_has_available_slots(calendar, current_pick)
        and ffighter_not_already_on_day(calendar, ffighter, current_pick)
        and rank_limitation_checks(calendar, ffighter, current_pick)
    ):
        return False

    # Send back OK to Assign the date if all checks are passed

    # ** with the implementation of this, we check increments while simultaniously approving.  We should really run a check that all increments are allowed
    process_pick_increments(calendar, ffighter, current_pick)
    
    return True

def process_ffighter_pick(calendar, rejected, ffighter):
    """Processes a single pick for the firefighter."""
    current_pick = ffighter.picks.pop(0)
    date_added = 0

    if validate_pick_with_reasoning(calendar, ffighter, current_pick):
        current_pick.determination = "Approved"
        # ** Processing the pick and granting approval should be the point that it is added to calendar
        date_added += 1
    else:
        current_pick.determination = "Rejected"
        rejected.setdefault(ffighter.name, []).append(current_pick.date)
    ffighter.processed.append(current_pick)
    return date_added

# Other Helpers
# =================================================================================================
def randomize_sub_priority(ffighters):
    """Randomizes the sub-priority of firefighters with matching hire dates."""
    for ffighter in ffighters:
        ffighter.dice = random.random()
    ffighters.sort(key=lambda x: (x.hireDate, x.dice))


# Calendar Formation
# =================================================================================================

def add_2_picks_for_ffighter(calendar, rejected, ffighter):
    """Attempts to add up to 2 picks for the firefighter."""
    dates_added = 0
    # while a firefighter has valid picks remaining, keep trying untill 2 are approved
    while dates_added < 2 and len(ffighter.picks) > 0:
        dates_added += process_ffighter_pick(calendar, rejected, ffighter)

def make_calendar(ffighters, silent_mode=False):
    """Analysis of firefighters picks: fully creates the calendar."""

    calendar = {}
    rejected = {}

    # untill all firefighters have a determination for all picks...
    while any(filter(lambda x: len(x.picks), ffighters)):
        randomize_sub_priority(ffighters)
        if not silent_mode:
            logger.info("Processing a round of picks...")
        # grant no more than 2 picks per person per round
        for ffighter in ffighters:
            add_2_picks_for_ffighter(calendar, rejected, ffighter)

    return {"calendar": calendar, "rejected": rejected}