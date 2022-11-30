import csv
from datetime import datetime
import random

date_format = '%m-%d-%Y'


class Pick:
    def __init__(self, date, type, determination="Unaddressed"):
        '''date, type, determination: defaults to "Unaddressed"'''
        self.date = date
        self.type = type
        self.determination = determination

    def __str__(self):
        return (f"{self.date} ({self.type:^10}) - {self.determination}")


class FFighter:
    def __init__(self, fname, lname, hireDate, picks):
        self.fname = fname
        self.lname = lname
        self.name = f"{lname}, {fname[0]}"
        self.hireDate = hireDate
        self.dice = random.random()
        self.processed = []
        self.picks = picks

    def __str__(self):
        return (f"f/lname: {self.fname} {self.lname}, prioity/priorityModifier : {self.priority} {self.priorityModifier}, hireDate : {self.hireDate}, picks : {self.picks}")


# ###########################################################################################################
#     Array Functionality
# ###########################################################################################################

def setPriorities(arr):
    """Take an array of FFighters.
        Orders by seniority, and sets the priority flag for each ffighter.
        Returns the sorted array of FFighters"""
    arr.sort(key=lambda x: (x.hireDate, x.dice))
    return arr


def printPriority(arr):
    for ffighter in arr:
        print(
            f'{ffighter.name:<20} : {str(ffighter.hireDate) :<10} - {ffighter.dice:> 20}')

# ================================================================


def makeCalendar(ffighters):
    """Analysis of firefighters picks:  fully creates the calendar"""

    calendar = {}
    rejected = {}

    #  Helper to add a date to the calendar
    def tryAddToCalendar(ffighter, current_pick):
        # add new date if needed
        if current_pick.date not in calendar.keys():
            calendar[current_pick.date] = [ffighter.name]
            return 1

        # add to date if possible
        if len(calendar[current_pick.date]) < 5:
            calendar[current_pick.date].append(ffighter.name)
            return 1

        return 0

    # while any firefighter still has an unaddressed picked day off...
    while any(filter(lambda x: len(x.picks), ffighters)):
        # Loop through each fire fighter, and add their day off requests in groups of 2
        for ffighter in ffighters:
            DatesAdded = 0
            while DatesAdded < 2 and len(ffighter.picks) > 0:
                current_pick = ffighter.picks.pop(0)

                if tryAddToCalendar(ffighter, current_pick):
                    current_pick.determination = "approved"
                    DatesAdded += 1
                else:
                    current_pick.determination = "rejected"
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
            # Rank
            startDate = row['Employee Start Date']
            # Years of Service
            # Day 1
            #  Type
            # Day 2
            # Type 2
            # naming pattern continues  to 18, except for the glitch on Type (1)
            # Shift
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
                FFighter(fname, lname, hireDate, pickDates))
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


def printDictionary(cal):
    """"""
    keylist = sorted(cal.keys())

    for key in keylist:
        print(f"{key}:\n   {cal[key]}\n")


def printCalendar(results: dict):
    '''Expects "results" dictionary returned from makeCalendar.
    Must contain 'calendar' key'''
    print('\n\n  --==     Calendar     ==--\n')
    printDictionary(results['calendar'])


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

    printFinal(ffighters)


if __name__ == '__main__':
    main()
