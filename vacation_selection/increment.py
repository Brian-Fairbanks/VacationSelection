# increment.py
from vacation_selection.setup_logging import setup_logging
logger = setup_logging('Increment')

# Increment Class
# ================================================================================================
class Increment:
    # Class-level configurations remain the same...
    max_total_ffighters_allowed = 5

    def __init__(self, date, name, only_increment=False ):
        self.date = date
        self.name = name
        self.only_increment = only_increment
        self.ffighters = []
        self.picks=[]
        self.rank_counts = {
            'Apparatus Specialist': 0,
            'Lieutenant': 0,
            'Captain': 0,
            'Battalion Chief': 0
        }
        self.denial_reason=""
    
    def write_to_row(self, writer):
        """Write the increment details to the CSV row."""
        # Prepare the list of firefighters with increment details
        if self.only_increment:
            # Include only the firefighter names with increments_plain_text()
            all_ffighters = [f"{ff.name} ({pick.increments_plain_text()})" for ff, pick in zip(self.ffighters, self.picks)]
            row = [self.date] + (all_ffighters + [""] * 5)[:5]
        else:
            # Include firefighter names with increment names
            all_ffighters = [f"{ff.name} ({pick.increments_plain_text()})" for ff, pick in zip(self.ffighters, self.picks)]
            row = [f"{self.date} ({self.name})"] + (all_ffighters + [""] * 5)[:5]

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
        max_firefighters_off = 5  # No dependencies
        max_apparatus_specialists_off = 5  # No dependencies
        max_lieutenants_off = 5 - num_captains
        max_captains_off = 3 - num_battalion_chiefs
        max_battalion_chiefs_off = min(2, 3 - num_captains)

        # Check limitations
        if rank == 'Apparatus Specialist':
            if num_apparatus_specialists >= max_apparatus_specialists_off:
                self.denial_reason = f"Increment already has {num_apparatus_specialists} Apparatus Specialists off"
                return True
        elif rank == 'Lieutenant':
            if num_lieutenants >= max_lieutenants_off:
                self.denial_reason = f"Increment already has {num_lieutenants} Lieutenants, {num_captains} Captains, and {num_battalion_chiefs} Battalion Chiefs off"
                return True
        elif rank == 'Captain':
            if num_captains >= max_captains_off:
                self.denial_reason = f"Increment already has {num_captains} Captains, {num_lieutenants} Lieutenants, and {num_battalion_chiefs} Battalion Chiefs off"
                return True
        elif rank == 'Battalion Chief':
            if num_battalion_chiefs >= max_battalion_chiefs_off:
                self.denial_reason = f"Increment already has {num_battalion_chiefs} Battalion Chiefs, {num_captains} Captains, and {num_lieutenants} Lieutenants off"
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
        self.ffighters.append(ffighter)
        # Update rank counts
        if ffighter.rank not in self.rank_counts:
            self.rank_counts[ffighter.rank] = 0
        self.rank_counts[ffighter.rank] += 1
        self.picks.append(ffighter.current_pick)
        return True
