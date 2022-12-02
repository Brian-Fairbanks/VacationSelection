import csv
from datetime import datetime
import random
from os import path, makedirs
import logging

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


class Pick:
    def __init__(self, date, type, determination="Unaddressed"):
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


def calendarToCSV(results: dict):
    '''Expects "results" dictionary returned from makeCalendar().
    Must contain 'calendar' key'''

    cal = results['calendar']
    logging.debug("Creating File...")

    with open(f'{writePath}/calendar-{runtime}.csv', 'w', newline='') as f:
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
            f'{ffighter.name:<20} ({len(ffighter.picks):>2}) : {str(ffighter.hireDate) :<10} - {ffighter.dice:< 20}')

# ================================================================


def makeCalendar(ffighters):
    """Analysis of firefighters picks:  fully creates the calendar"""

    calendar = {}
    rejected = {}

    #  Helper to add a date to the calendar
    # ----------------------------------------------------------------
    def tryAddToCalendar(ffighter, current_pick):

        # see if the date can even be added to begin with
        if ffighter.rank == "Probationary Firefighter":
            # print(f'{current_pick.type} :  {current_pick.date} -  {ffighter.hireDate}    =  {(current_pick.date-ffighter.hireDate).days}')
            if (current_pick.type == "Holiday") and ((current_pick.date-ffighter.hireDate).days) < 182:
                current_pick.reason = {"Holiday < 182 Days from Hire Date"}
                return 0
            if (current_pick.type == "Vacation") & ((current_pick.date-ffighter.hireDate).days) < 365:
                current_pick.reason = {"Vacation < 365 Days from Hire Date"}
                return 0

        # add new date if needed
        if current_pick.date not in calendar.keys():
            calendar[current_pick.date] = [ffighter]
            return 1

        # add to date if possible
        if len(calendar[current_pick.date]) < 5:
            calendar[current_pick.date].append(ffighter)
            return 1
        else:
            current_pick.reason = "Day already has 5 members off"

        return 0

    # Loop through every Pick, and insert into hashing calender, or justify decision
    # --------------------------------------------------------------------------------------

    # while any firefighter still has an unaddressed picked day off...
    while any(filter(lambda x: len(x.picks), ffighters)):
        # Randomize firefighters with matching hire dates
        randomizeSubPriority(ffighters)
        printPriority(ffighters)
        # Loop through each fire fighter, and add their day off requests in groups of 2
        for ffighter in ffighters:
            DatesAdded = 0
            while DatesAdded < 2 and len(ffighter.picks) > 0:
                current_pick = ffighter.picks.pop(0)

                if tryAddToCalendar(ffighter, current_pick):
                    current_pick.determination = "Approved"
                    DatesAdded += 1
                else:
                    current_pick.determination = "Rejected"
                    # mark date in hash table as rejected
                    try:
                        rejected[ffighter.name].append(current_pick.date)
                    except:
                        rejected[ffighter.name] = [current_pick.date]
                ffighter.processed.append(current_pick)
        #
    #
    return {"calendar": calendar, "rejected": rejected}


# ###########################################################################################################
#     Initial Access of data
# ###########################################################################################################

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
            rank = row["Rank"]
            startDate = row['Employee Start Date']
            # Years of Service
            # Day 1
            #  Type
            # Day 2
            # Type 2
            # naming pattern continues  to 18, except for the glitch on Type (1)
            shift = row["Shift"]
            # Submission ID

            pickDates = []
            for x in range(1, 18):
                try:
                    date = row[f"Day {x}"]
                    if x != 1:
                        type = row[f"Type {x}"]
                    else:
                        type = row[" Type"]
                    # pickDates.append(datetime.strptime(
                    #     date, date_format).date())
                    pickDates.append(
                        Pick(datetime.strptime(date, date_format).date(), type))
                except:
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
            f'{ffighter.name:<20} :')
        for key in ffighter.processed:
            print(key)

# ##############################################################################################################################################
#     Main Code
# ##############################################################################################################################################


def main():
    # ffighters = setPriorities(getData('testForms.csv'))
    ffighters = setPriorities(getData('Early_Form_Pull.csv'))
    # printPriority(ffighters)

    # Note that DICTS, LISTS, and SETS are mutable, and so pass by reference, not pass by value like ints and setPriorities
    # IE, ffighter objects changes
    results = makeCalendar(ffighters)

    # printCalendar(results)
    # printRejected(results)

    # printFinal(ffighters)
    calendarToCSV(results)


if __name__ == '__main__':
    main()
