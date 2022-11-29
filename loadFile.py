import csv
from datetime import datetime


class Pick:
    def __init__(self, date, type, determination="Unaddressed"):
        self.date = date
        self.type = type
        self.determination = determination

    def __str__(self):
        return (f"{self.date}({self.type}) - {self.determination}")


class FFighter:
    def __init__(self, fname, lname, hireDate, picks):
        self.fname = fname
        self.lname = lname
        self.name = f"{lname}, {fname[0]}"
        self.hireDate = hireDate
        self.originalPicks = picks
        self.picks = picks
        self.picksDetermination = {}
        self.priority = None    # default seniority
        self.cycleSkip = 0  # temporary modifier to account for wonky logic

    def __str__(self):
        return (f"f/lname: {self.fname} {self.lname}, prioity/priorityModifier : {self.priority} {self.priorityModifier}, hireDate : {self.hireDate}, picks : {self.picks}")


# ###########################################################################################################
#     Array Functionality
# ###########################################################################################################

def setPriorities(arr):
    """Take an array of FFighters.
        Orders by seniority, and sets the priority flag for each ffighter.
        Returns the sorted array of FFighters"""
    arr.sort(key=lambda x: x.hireDate)

    # strange that n, firefighter doesnt seem to work...  implementing manual indexing methods...
    for n, ffighter in enumerate(arr):
        # print(f"{n} {ffighter.hireDate}")
        # store this seniority order as priority
        ffighter.priority = n
    return arr

# ================================================================


def printDictionary(cal):
    """"""
    keylist = sorted(cal.keys())

    for key in keylist:
        print(f"{key}:\n   {cal[key]}\n")

# ================================================================


def makeCalendar(ffighters):
    """Analysis of firefighters picks:  fully creates the calendar"""

    calendar = {}
    rejected = {}

    #  Helper to add a date to the calendar
    def tryAddToCalendar(ffighter, current_pick):
        # add new date if needed
        if current_pick not in calendar.keys():
            calendar[current_pick] = [ffighter.name]
            return 1

        # add to date if possible
        if len(calendar[current_pick]) < 5:
            calendar[current_pick].append(ffighter.name)
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
                    ffighter.picksDetermination[current_pick] = "approved"
                    DatesAdded += 1
                else:
                    ffighter.picksDetermination[current_pick] = "rejected"
                    # mark date in hash table as rejected
                    try:
                        rejected[ffighter.name].append(current_pick)
                    except:
                        rejected[ffighter.name] = [current_pick]
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
            # There has got to be a better way to do this....
            # why wont referencing columns by index work?
            picks = [
                row['1st'],
                row['2nd'],
                row['3rd'],
                row['4th'],
                row['5th'],
                row['6th'],
                row['7th'],
                row['8th'],
                row['9th'],
                row['10th'],
                row['11th'],
                row['12th'],
                row['13th'],
                row['14th'],
                row['15th'],
                row['16th'],
                row['17th'],
                row['18th']
            ]

            pickDates = []
            for date in picks:
                try:
                    pickDates.append(datetime.strptime(
                        date, '%m/%d/%Y').date())
                except:
                    pass

            hireDate = datetime.strptime(row['HIRE DATE'], '%m/%d/%Y').date()
            ffdata.append(
                FFighter(row['Name'], row['LNAME'], hireDate, pickDates))
    return ffdata


# ##############################################################################################################################################
#     Main Code
# ##############################################################################################################################################

def main():
    # ffighters = getData('testForms.csv')
    # for ffighter in ffighters:
    #     print(ffighter)
    ffighters = setPriorities(getData('testForms.csv'))
    # for ffighter in ffighters:
    #     print(ffighter)
    results = makeCalendar(ffighters)

    print('\n\n  --==     Calendar     ==--\n')
    printDictionary(results['calendar'])

    print('\n\n  --==  Rejected Dates  ==--\n')
    # print(results['rejected'])
    for key in results['rejected']:
        print(f"{key} : {results['rejected'][key]}")

    print('\n\n  --==  Final Results   ==--\n')
    for ffighter in ffighters:
        print(
            f'{ffighter.name:<20} :')
        for key in ffighter.picksDetermination:
            print(f"   {key} : {ffighter.picksDetermination[key]}")


if __name__ == '__main__':
    main()
