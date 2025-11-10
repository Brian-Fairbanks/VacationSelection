import csv
from datetime import datetime
import random
from os import path, makedirs
import logging
import difflib

runtime = datetime.now().strftime("%Y.%m.%d %H.%M")

# set up logging folder
writePath = "./output"
if not path.exists(writePath):
    makedirs(writePath)


# logging setup - write to output file as well as printing visably
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler(
    f'{writePath}/RunLog-{runtime}.log', 'a'))
print = logger.info

# date format
date_format = '%m-%d-%Y'

def calculate_max_shifts_off(hire_date):
    """Calculate the maximum number of shifts off allowed based on years of service."""
    years_of_service = (datetime.now().date() - hire_date).days // 365

    if years_of_service < 1:
        return 7  # Example: 1 year or less gets 7 shifts off
    elif 1 <= years_of_service < 5:
        return 14  # Example: 1-5 years get 14 shifts off
    elif 5 <= years_of_service < 10:
        return 21  # Example: 5-10 years get 21 shifts off
    else:
        return 28  # Example: 10+ years get 28 shifts off
    
class Pick:
    def __init__(self, date, type="U", determination="Unaddressed"):
        '''date, type, determination: defaults to "Unaddressed"'''
        self.date = date
        self.type = type
        self.determination = determination
        self.reason = None

    def __str__(self):
        ret = f"{self.date} ({self.type:^10}) - {self.determination}"
        if self.reason:
            ret += f' ({self.reason})'
        return ret


class FFighter:
    def __init__(self, fname, lname, hireDate, rank, shift,  picks):
        self.fname = fname
        self.lname = lname
        self.name = f"{lname}, {fname[0]}"
        self.rank = rank
        self.shift = shift
        self.hireDate = hireDate
        self.dice = random.random()
        self.processed = []
        self.picks = picks
        self.max_shifts_off = calculate_max_shifts_off(hireDate)

    def printPicks(self):
        results = ""
        for pick in self.picks:
            results += str(pick)+", "
        return results

    def __str__(self):
        # return (f"f/lname: {self.fname} {self.lname}, prioity/priorityModifier : {self.priority} {self.priorityModifier}, hireDate : {self.hireDate}, picks : {self.picks}")
        return self.name


# ###########################################################################################################
#     Calendar Handling
# ###########################################################################################################

def printDictionary(cal):
    """"""
    keylist = sorted(cal.keys())

    for key in keylist:
        print(f"{key}:\n   {cal[key]}\n")


def printCalendar(results: dict):
    '''Expects "results" dictionary returned from makeCalendar().
    Must contain 'calendar' key'''
    print('\n\n  --==     Calendar     ==--\n')
    printDictionary(results['calendar'])


def calendarToCSV(results: dict, suffix):
    '''Expects "results" dictionary returned from makeCalendar().
    Must contain 'calendar' key'''

    cal = results['calendar']
    logging.debug("Creating File...")

    with open(f'{writePath}/{runtime}-calendar-{suffix}.csv', 'w', newline='') as f:
        logging.debug("Writing to File...")

        try:
            # create the csv writer
            writer = csv.writer(f)

            # Format Header
            header = ['Date', "First", "Second", "Third", "Fourth", "Fifth"]
            writer.writerow(header)

            # order the calendar
            keylist = sorted(cal.keys())

            for key in keylist:
                writer.writerow([key]+cal[key])

        except Exception as Argument:
            logging.exception(f"Failed to write to file.\n")
    logging.debug("File finished writing.")


# ###########################################################################################################
#     Array Functionality
# ###########################################################################################################

def setPriorities(arr):
    """Take an array of FFighters.
        Orders by seniority, and sets the priority flag for each ffighter.
        Returns the sorted array of FFighters"""
    arr.sort(key=lambda x: (x.hireDate, x.dice))
    return arr


def randomizeSubPriority(arr):
    """Take an array of FFighters.
        Randomize the sorting subpriority, then reorder list
    """
    for ffighter in arr:
        ffighter.dice = random.random()
    setPriorities(arr)
    return arr


def printPriority(arr):
    print(f"\n---=== Priority List at {datetime.now()} ===---\n")
    for ffighter in arr:
        print(
            f'{ffighter.name:<20} : {str(ffighter.hireDate) :<10} - {ffighter.dice:< 22} :: [{ffighter.printPicks()}]')

# ================================================================


def makeCalendar(ffighters, silent_mode=False):
    """Analysis of firefighters picks:  fully creates the calendar"""

    calendar = {}
    rejected = {}

    #  Helper to add a date to the calendar
    # ----------------------------------------------------------------
    def try_to_add_to_calendar(ffighter, current_pick):

        # deny probies within exclusion ranges
        if ffighter.rank == "Probationary Firefighter":
            if (current_pick.type == "Holiday") and ((current_pick.date - ffighter.hireDate).days) < 182:
                current_pick.reason = "Holiday < 182 Days from Hire Date"
                return 0
            if (current_pick.type == "Vacation") and ((current_pick.date - ffighter.hireDate).days) < 365:
                current_pick.reason = "Vacation < 365 Days from Hire Date"
                return 0

        # aside from those probies, grant it if the date hasnt ever been picked.  Full stop
        if current_pick.date not in calendar.keys():
            calendar[current_pick.date] = [ffighter]
            return 1

         # Check if the firefighter is already in the list for the current pick date
        if ffighter in calendar.get(current_pick.date, []):
            current_pick.reason = "Already requested this day off"
            return 0

        # Define a function to count firefighters of specific rank(s) off on the current_pick day

        def count_rank_off(ranks):
            return len(list(filter(lambda x: (x.rank in ranks), calendar[current_pick.date])))

        # Specify current staffing counts
        num_apparatus_specialists = count_rank_off(["Apparatus Specialist"])
        num_lieutenants = count_rank_off(["Lieutenant"])
        num_captains = count_rank_off(["Captain"])
        num_battalion_chiefs = count_rank_off(["Battalion Chief"])

        # Specify max shifts off for each rank based on the specified rules
        max_apparatus_specialists_off = 5
        max_lieutenants_off = 5 - num_captains
        max_captains_off = 3 - num_battalion_chiefs
        # starting with the second captain, each one decreases the amount of BCs
        max_battalion_chiefs_off = min(2, 3 - num_captains)

        # Check if the firefighter's rank and the current count violate the rules
        if ffighter.rank == "Apparatus Specialist":
            if num_apparatus_specialists >= max_apparatus_specialists_off:
                current_pick.reason = f"Day already has {num_apparatus_specialists} Apparatus Specialists off"
                return 0

        if ffighter.rank == "Lieutenant":
            if num_lieutenants >= max_lieutenants_off:
                current_pick.reason = f"Day already has {num_lieutenants} Lieutenants and {num_captains} Captains off"
                return 0

        if ffighter.rank == "Captain":
            if num_captains >= max_captains_off:
                current_pick.reason = f"Day already has {num_captains} Captains, {num_lieutenants} Lieutenants, and {num_battalion_chiefs} Battalion Chiefs off"
                return 0

        if ffighter.rank == "Battalion Chief":
            if num_battalion_chiefs >= max_battalion_chiefs_off:
                current_pick.reason = f"Day already has {num_battalion_chiefs} Battalion Chiefs and {num_captains} Captains off"
                return 0

        if len(calendar[current_pick.date]) >= 5:
            current_pick.reason = "Day already has 5 members off"
            return 0

        # Made it through the Rule Gauntlet. Award the date
        calendar[current_pick.date].append(ffighter)
        return 1

    # Loop through every Pick, and insert into hashing calender, or justify decision
    # --------------------------------------------------------------------------------------

    # -- process a single pick
    def process_ffighter_pick(ffighter):
        ''' Take a given firefighter, take their number one pick off of their pick list.
            try to add it to the calendar if possible '''
        current_pick = ffighter.picks.pop(0)
        dateAdded = 0

        if try_to_add_to_calendar(ffighter, current_pick):
            current_pick.determination = "Approved"
            dateAdded += 1
        else:
            current_pick.determination = "Rejected"
            # mark date in hash table as rejected
            try:
                rejected[ffighter.name].append(current_pick.date)
            except:
                rejected[ffighter.name] = [current_pick.date]
        ffighter.processed.append(current_pick)
        return dateAdded

    # -- process as many picks as needed for a ffighters round
    def add_2_picks_for_ffighter(ffighter):
        ''' Take a firefigher, and process_ffighter_pick
           Repeat until you assign 2, or their list is depleated '''

        DatesAdded = 0
        while DatesAdded < 2 and len(ffighter.picks) > 0:
            DatesAdded += process_ffighter_pick(ffighter)

    # -- Coordinate all ffighters draft rounds
    # while any firefighter still has an unaddressed picked day off...
    while any(filter(lambda x: len(x.picks), ffighters)):
        # Randomize firefighters with matching hire dates
        randomizeSubPriority(ffighters)
        if not silent_mode:
            printPriority(ffighters)
        # Loop through each fire fighter, and draft their picks
        for ffighter in ffighters:
            add_2_picks_for_ffighter(ffighter)

    # -- Return completed Calendar and Rejections
    return {"calendar": calendar, "rejected": rejected}


# ###########################################################################################################
#     Initial Access of data
# ###########################################################################################################
ranks = [
    "Firefighter",
    "Probationary Firefighter",
    "Apparatus Specialist",
    "Lieutenant",
    "Captain",
    "Battalion Chief",
]


def ensure_rank(rank):
    res = check_rank(rank)
    if res == None:
        exit(1)
    return res


def check_rank(rank):
    # Check if the provided rank is in the list of valid ranks

    if rank in ranks:
        return rank

    # If not, find the closest match in the list
    close_matches = difflib.get_close_matches(rank, ranks, n=1, cutoff=0.01)
    accuracy = difflib.SequenceMatcher(None, rank, close_matches[0]).ratio()

    if close_matches and accuracy >= 0.75:
        # If a close match is found and it's sufficiently accurate, use it
        print(
            f"'{rank}' is not a valid rank. Replacing to '{close_matches[0]}' with {accuracy} certainty.")
        return close_matches[0]
    else:
        # If no close match or not accurate enough, raise an error
        print(
            f"\nERROR: '{rank}' is not a valid rank. Presumably '{close_matches[0]}' but only {accuracy} certainty.\n\t- Please correct the file and reprocess.")
        return None


def getData(filename):
    '''Read CSV file, and drop the results into an arrray of FFighter class
    '''
    ffdata = []

    with open(filename, mode="r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # listing every column in the form to ease consistancy

            # Submission Date
            fname = row['First Name']
            lname = row['Last Name']
            # Today's Date
            # Employee ID #
            rank = ensure_rank(row["Rank"])
            startDate = row['Employee Start Date']
            # Years of Service
            # Day 1
            # Type 1  :  ' Type' for older files
            # Day 2
            # Type 2
            # naming pattern continues  to 18, except for the glitch on Type (1)
            shift = row["Shift"]
            # Submission ID

            pickDates = []
            for x in range(1, 40):
                date = row[f"Day {x}"]
                try:
                    # pickDates.append(datetime.strptime(
                    #     date, date_format).date())
                    pickDates.append(
                        Pick(datetime.strptime(date, date_format).date(), "U"))
                except Exception as Argument:
                    if date != "":
                        logging.exception(f"{date}")
                    # print(f'\nERROR - {row[f"Day {x}"]}: {e}\n')
                    pass

            hireDate = datetime.strptime(
                startDate, date_format).date()
            ffdata.append(
                FFighter(fname, lname, hireDate, rank, shift, pickDates))
    return ffdata


# ###########################################################################################################
#     Testing and Printing Functions
# ###########################################################################################################
def printRejected(results: dict):
    '''Expects "results" dictionary returned from makeCalendar.
    Must contain 'rejected' key'''
    print('\n\n  --==  Rejected Dates  ==--\n')
    # print(results['rejected'])
    for key in results['rejected']:
        print(f"{key} : {results['rejected'][key]}")


def printFinal(ffighters: dict):
    print('\n\n  --==  Final Results   ==--\n')
    for ffighter in ffighters:
        print(
            f'{ffighter.name:<20} : \n{ffighter.hireDate} - ({ffighter.shift}) {ffighter.rank}')
        for key in ffighter.processed:
            print(key)


def picksToCSV(ffighter: list, suffix):

    logging.debug("Creating File...")

    temp = []
    temp.extend(ffighter)

    with open(f'{writePath}/{runtime}-FFighters-{suffix}.csv', 'w', newline='') as f:
        logging.debug("Writing to File...")

        try:
            # create the csv writer
            writer = csv.writer(f)

            # order the calendar
            temp.sort(key=lambda x: x.name)

            header = ['Name', "Rank", "Date Requested",
                      "Type", "Determination", "Reason"]
            writer.writerow(header)

            for ffighter in temp:
                writer.writerow([ffighter.name, ffighter.rank])
                for key in ffighter.processed:
                    writer.writerow(
                        ['', '', key.format_date_display(), key.type, key.determination, key.reason])
                writer.writerow([])

        except Exception as Argument:
            logging.exception(f"Failed to write to file.\n")
    logging.debug("File finished writing.")

# ##############################################################################################################################################
#     Main Code
# ##############################################################################################################################################


def main():
    ffighters = setPriorities(
        getData('2024 VACATION REQUEST FORM - Form Responses.csv'))

    # Note that DICTS, LISTS, and SETS are mutable, and so pass by reference, not pass by value like ints and setPriorities
    # IE, ffighter objects changes

    for shift in ["A", "B", "C"]:

        shiftMembers = list(filter(lambda x: x.shift == shift, ffighters))
        results = makeCalendar(shiftMembers)

        # printCalendar(results)
        # printRejected(results)

        printFinal(shiftMembers)
        calendarToCSV(results, shift)
        picksToCSV(shiftMembers, shift)


if __name__ == '__main__':
    main()
