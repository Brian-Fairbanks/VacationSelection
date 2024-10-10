from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')

import random

def probationary_limitations(ffighter, current_pick):
    """Checks if probationary firefighters are restricted from taking the day off."""
    if ffighter.rank == "Probationary Firefighter":
        if (current_pick.type == "Holiday") and ((current_pick.date - ffighter.hireDate).days < 182):
            current_pick.reason = "Holiday < 182 Days from Hire Date"
            return True
        if (current_pick.type == "Vacation") and ((current_pick.date - ffighter.hireDate).days < 365):
            current_pick.reason = "Vacation < 365 Days from Hire Date"
            return True
    return False

def has_reached_max_days(ffighter, current_pick):
    """Checks if the firefighter has reached their maximum allowed days off."""
    if ffighter.approved_days_count >= ffighter.max_days_off:
        current_pick.reason = "Max days off already reached"
        return True
    return False

def day_has_available_slots(calendar, current_pick):
    """Checks if the day has any available slots left."""
    if current_pick.date not in calendar:
        calendar[current_pick.date] = [None, None]  # Default to two halves (AM and PM)

    total_approved = sum(1 for slot in calendar[current_pick.date] if slot is not None)
    if total_approved >= 5:
        current_pick.reason = "Day already has 5 members off"
        return False
    return True

def firefighter_already_approved(calendar, ffighter, current_pick):
    """Checks if the firefighter is already approved for the requested day."""
    if ffighter in [x['ffighter'] for x in calendar.get(current_pick.date, []) if x]:
        current_pick.reason = "Already requested this day off"
        return True
    return False

def rank_limitation_checks(calendar, ffighter, current_pick):
    """Checks if adding the firefighter would exceed the rank limitations for the day."""
    def count_rank_off(ranks):
        return sum(1 for value in calendar[current_pick.date] if value and value['ffighter'].rank in ranks)

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
    if date not in calendar:
        calendar[date] = [None, None]  # Default to two halves (AM and PM)

    for i, increment in enumerate(increments):
        if increment == 1 and calendar[date][i] is None:
            calendar[date][i] = {"ffighter": ffighter, "pick": current_pick}
            ffighter.approved_days_count += 0.5

def try_to_add_to_calendar(calendar, rejected, ffighter, current_pick):
    """Attempts to add the current pick to the calendar."""
    # Immediate Failures
    if probationary_limitations(ffighter, current_pick):
        return 0
    if has_reached_max_days(ffighter, current_pick):
        return 0
    if not day_has_available_slots(calendar, current_pick):
        return 0
    if firefighter_already_approved(calendar, ffighter, current_pick):
        return 0
    if not rank_limitation_checks(calendar, ffighter, current_pick):
        return 0

    # Assign the date if all checks are passed
    process_pick_increments(calendar, ffighter, current_pick)
    return 1

def process_ffighter_pick(calendar, rejected, ffighter):
    """Processes a single pick for the firefighter."""
    current_pick = ffighter.picks.pop(0)
    date_added = 0

    if try_to_add_to_calendar(calendar, rejected, ffighter, current_pick):
        current_pick.determination = "Approved"
        date_added += 1
    else:
        current_pick.determination = "Rejected"
        rejected.setdefault(ffighter.name, []).append(current_pick.date)
    ffighter.processed.append(current_pick)
    return date_added

def add_2_picks_for_ffighter(calendar, rejected, ffighter):
    """Attempts to add up to 2 picks for the firefighter."""
    dates_added = 0
    while dates_added < 2 and len(ffighter.picks) > 0:
        dates_added += process_ffighter_pick(calendar, rejected, ffighter)

def randomize_sub_priority(ffighters):
    """Randomizes the sub-priority of firefighters with matching hire dates."""
    for ffighter in ffighters:
        ffighter.dice = random.random()
    ffighters.sort(key=lambda x: (x.hireDate, x.dice))

def make_calendar(ffighters, silent_mode=False):
    """Analysis of firefighters picks: fully creates the calendar."""

    calendar = {}
    rejected = {}

    while any(filter(lambda x: len(x.picks), ffighters)):
        randomize_sub_priority(ffighters)
        if not silent_mode:
            logger.info("Processing a round of picks...")
        for ffighter in ffighters:
            if ffighter.approved_days_count < ffighter.max_days_off:
                add_2_picks_for_ffighter(calendar, rejected, ffighter)

    return {"calendar": calendar, "rejected": rejected}