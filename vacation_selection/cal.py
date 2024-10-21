from vacation_selection.setup_logging import setup_logging
logger = setup_logging('calendar')

import random

# Day Class
# ================================================================================================
class Day:
    # Class-level configurations remain the same...
    single_day_increment = True
    if single_day_increment:
        max_total_ffighters_allowed = 5
    max_total_ffighters_allowed = 10

    def __init__(self, date):
        self.date = date
        self.ffighters = []
        self.rank_counts = {
            'Apparatus Specialist': 0,
            'Lieutenant': 0,
            'Captain': 0,
            'Battalion Chief': 0
        }
        if self.single_day_increment:
            self.increments = {'ALL':[]}
        else:
            self.increments = {'AM': [], 'PM': []}
        self.denial_reason = ''  # Attribute to store denial reasons

    @staticmethod
    def get_header():
        if Day.single_day_increment:
            header = ['Date', 'Shift', 'First', 'Second', 'Third', 'Fourth', 'Fifth']
        else:
            header = ['Date', 'Shift', 'First', 'Second', 'Third', 'Fourth', 'Fifth']
        return header
    
    def write_to_row(self, writer):
        if Day.single_day_increment:
            # Handle the single increment case
            all_ffighters = [f"{ff.name} ({inc})" for ff, inc in self.increments.get('ALL', [])]
            row = [self.date, " (ALL)"] + (all_ffighters + [""] * 5)[:5]
            writer.writerow(row)
        else:
            # Handle multi-increment case as before
            am_ffighters = [ffighter.name for ffighter in self.increments.get('AM', [])]
            am_row = [self.date, " (AM)"] + (am_ffighters + [""] * 5)[:5]
            writer.writerow(am_row)

            pm_ffighters = [ffighter.name for ffighter in self.increments.get('PM', [])]
            pm_row = [self.date, " (PM)"] + (pm_ffighters + [""] * 5)[:5]
            writer.writerow(pm_row)


    def is_full(self):
        isfull = len(self.ffighters) >= Day.max_total_ffighters_allowed
        if isfull: self.denial_reason = "Maximim amount of requests already approved"
        return isfull
        

    def can_add_rank(self, rank):
        # Current counts
        num_apparatus_specialists = self.rank_counts['Apparatus Specialist']
        num_lieutenants = self.rank_counts['Lieutenant']
        num_captains = self.rank_counts['Captain']
        num_battalion_chiefs = self.rank_counts['Battalion Chief']

        # Calculate maximums
        max_firefighters_off = 5  # No dependencies
        max_apparatus_specialists_off = 5  # No dependencies
        max_lieutenants_off = 5 - num_captains
        max_captains_off = 3 - num_battalion_chiefs
        max_battalion_chiefs_off = min(2, 3 - num_captains)

        # Check limitations
        if rank == 'Apparatus Specialist':
            if num_apparatus_specialists >= max_apparatus_specialists_off:
                self.denial_reason = f"Day already has {num_apparatus_specialists} Apparatus Specialists off"
                return False
        elif rank == 'Lieutenant':
            if num_lieutenants >= max_lieutenants_off:
                self.denial_reason = f"Day already has {num_lieutenants} Lieutenants and {num_captains} Captains off"
                return False
        elif rank == 'Captain':
            if num_captains >= max_captains_off:
                self.denial_reason = f"Day already has {num_captains} Captains and {num_battalion_chiefs} Battalion Chiefs off"
                return False
        elif rank == 'Battalion Chief':
            if num_battalion_chiefs >= max_battalion_chiefs_off:
                self.denial_reason = f"Day already has {num_battalion_chiefs} Battalion Chiefs and {num_captains} Captains off"
                return False
        else:
            # For ranks without specific limitations, allow by default
            return True

        # Allow addition if no limitations are exceeded
        return True

    def has_ffighter(self, ffighter):
        check = ffighter in self.ffighters
        if check:self.denial_reason = "Already requested this day off"
        return check


    def add_single_increment(self, ffighter):
        # Add the firefighter with their increment info as a tuple
        self.increments['ALL'].append((ffighter, ffighter.current_pick.increments_plain_text()))
        return True
    
    def add_multi_increment(self, ffighter):
        # Store increment information
        increments = ffighter.current_pick.increments  # Assuming increments is a list like [1, 0] for AM only
        if increments[0] == 1:
            self.increments['AM'].append(ffighter)
        if increments[1] == 1:
            self.increments['PM'].append(ffighter)
        
    def add_ffighter(self, ffighter):
        self.ffighters.append(ffighter)
        # Update rank counts
        if ffighter.rank not in self.rank_counts:
            self.rank_counts[ffighter.rank] = 0
        self.rank_counts[ffighter.rank] += 1

        if self.single_day_increment:
            self.add_single_increment(ffighter)
        else:
            self.add_multi_increment(ffighter)

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


def validate_pick_with_reasoning(ffighter, calendar, rejected):
    """Validates a pick, and assigns a reason if failure"""

    # Immediate Failures for probationary limitations and max days off
    if probationary_limitations(ffighter, rejected) or has_reached_max_days(ffighter, rejected):
        return False
    
    # Set up date
    date = ffighter.current_pick.date
    if date not in calendar:
        calendar[date] = Day(date)
    day = calendar[date]

    # Validate other conditions before proceeding with the pick
    if day.is_full():
        reason = getattr(day, 'denial_reason', "Day already has maximum firefighters off")
        deny_ffighter_pick(ffighter, rejected, reason)
        return False
    if not day.can_add_rank(ffighter.rank):
        reason = getattr(day, 'denial_reason', "Day already has maximum firefighters off")
        deny_ffighter_pick(ffighter, rejected, reason)
        return False
    if day.has_ffighter(ffighter):
        reason = getattr(day, 'denial_reason', "Firefighter has already requested this day off")
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