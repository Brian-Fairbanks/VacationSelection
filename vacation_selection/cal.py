from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')

import random

def make_calendar(ffighters, silent_mode=False):
    """Analysis of firefighters picks: fully creates the calendar."""

    calendar = {}
    rejected = {}

    # Helper function to add a date to the calendar
    def try_to_add_to_calendar(ffighter, current_pick):
        # Deny probationary firefighters within exclusion ranges
        if ffighter.rank == "Probationary Firefighter":
            if (current_pick.type == "Holiday") and ((current_pick.date - ffighter.hireDate).days < 182):
                current_pick.reason = "Holiday < 182 Days from Hire Date"
                return 0
            if (current_pick.type == "Vacation") and ((current_pick.date - ffighter.hireDate).days < 365):
                current_pick.reason = "Vacation < 365 Days from Hire Date"
                return 0

        # Grant the date if it hasn't been picked by anyone yet
        if current_pick.date not in calendar:
            calendar[current_pick.date] = [ffighter]
            return 1

        # Check if the firefighter is already in the list for the current date
        if ffighter in calendar.get(current_pick.date, []):
            current_pick.reason = "Already requested this day off"
            return 0

        # Define a function to count firefighters of specific rank(s) off on the current pick day
        def count_rank_off(ranks):
            return len([x for x in calendar[current_pick.date] if x.rank in ranks])

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
            return 0
        if ffighter.rank == "Lieutenant" and num_lieutenants >= max_lieutenants_off:
            current_pick.reason = f"Day already has {num_lieutenants} Lieutenants and {num_captains} Captains off"
            return 0
        if ffighter.rank == "Captain" and num_captains >= max_captains_off:
            current_pick.reason = f"Day already has {num_captains} Captains, {num_lieutenants} Lieutenants, and {num_battalion_chiefs} Battalion Chiefs off"
            return 0
        if ffighter.rank == "Battalion Chief" and num_battalion_chiefs >= max_battalion_chiefs_off:
            current_pick.reason = f"Day already has {num_battalion_chiefs} Battalion Chiefs and {num_captains} Captains off"
            return 0

        if len(calendar[current_pick.date]) >= 5:
            current_pick.reason = "Day already has 5 members off"
            return 0

        # Assign the date if all checks are passed
        calendar[current_pick.date].append(ffighter)
        return 1

    # Processing logic for firefighter picks
    def process_ffighter_pick(ffighter):
        current_pick = ffighter.picks.pop(0)
        date_added = 0

        if try_to_add_to_calendar(ffighter, current_pick):
            current_pick.determination = "Approved"
            date_added += 1
        else:
            current_pick.determination = "Rejected"
            rejected.setdefault(ffighter.name, []).append(current_pick.date)
        ffighter.processed.append(current_pick)
        return date_added

    def add_2_picks_for_ffighter(ffighter):
        dates_added = 0
        while dates_added < 2 and len(ffighter.picks) > 0:
            dates_added += process_ffighter_pick(ffighter)

    def randomize_sub_priority(ffighters):
        """Randomizes the sub-priority of firefighters with matching hire dates."""
        for ffighter in ffighters:
            ffighter.dice = random.random()
        ffighters.sort(key=lambda x: (x.hireDate, x.dice))

    while any(filter(lambda x: len(x.picks), ffighters)):
        randomize_sub_priority(ffighters)
        if not silent_mode:
            logger.info("Processing a round of picks...")
        for ffighter in ffighters:
            add_2_picks_for_ffighter(ffighter)

    return {"calendar": calendar, "rejected": rejected}