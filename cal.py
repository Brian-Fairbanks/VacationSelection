# cal.py
import logging
import firefighter

def try_to_add_to_calendar(ffighter, current_pick, calendar):
    # Logic to add picks to the calendar based on staffing rules
    # Implement the logic here with rules for each firefighter rank
    pass

def make_calendar(ffighters, silent_mode=False):
    calendar = {}
    rejected = {}

    def process_ffighter_pick(ffighter):
        current_pick = ffighter.picks.pop(0)
        date_added = try_to_add_to_calendar(ffighter, current_pick, calendar)
        if date_added:
            current_pick.determination = "Approved"
        else:
            current_pick.determination = "Rejected"
            rejected.setdefault(ffighter.name, []).append(current_pick.date)
        ffighter.processed.append(current_pick)
        return date_added

    while any(filter(lambda x: len(x.picks), ffighters)):
        # Randomize subpriority if needed, then assign picks
        for ffighter in ffighters:
            while len(ffighter.picks) > 0:
                process_ffighter_pick(ffighter)
    
    return {"calendar": calendar, "rejected": rejected}

def print_dictionary(cal):
    for key in sorted(cal.keys()):
        print(f"{key}:\n   {cal[key]}\n")