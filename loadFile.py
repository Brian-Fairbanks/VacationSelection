import csv
from datetime import datetime
import itertools


class FFighter:
    def __init__(self, fname, lname, hire_date, picks):
        self.fname = fname
        self.lname = lname
        self.name = f"{lname}, {fname[0]}"
        self.hire_date = hire_date
        self.picks = picks
        self.picksDetermination = []
        self.priority = None    # default seniority
        self.priorityModifier = 0  # temporary modifier to account for wonky logic

    def __str__(self):
        return (f"f/lname: {self.fname} {self.lname}, prioity/priorityModifier : {self.priority} {self.priorityModifier}, hire_date : {self.hire_date}, picks : {self.picks}")


# ###########################################################################################################
#     Array Functionality
# ###########################################################################################################

def setPriorities(arr):
    """Take an array of FFighters.
        Orders by seniority, and sets the priority flag for each ffighter.
        Returns the sorted array of FFighters"""
    arr.sort(key=lambda x: x.hire_date)

    # strange that n, firefighter doesnt seem to work...  implementing manual indexing methods...
    for n, ffighter in enumerate(arr):
        # print(f"{n} {ffighter.hire_date}")
        # store this seniority order as priority
        ffighter.priority = n
    return arr


def recheckPriorities(arr):
    arr.sort(key=lambda x: x.priority-x.priorityModifier)
    return arr


def clearPriorityModifiers(arr):
    for ffighter in arr:
        ffighter.priorityModifier = 0


def printDictionary(cal):
    keylist = sorted(cal.keys())

    for key in keylist:
        print(f"{key}:\n   {cal[key]}\n")


def toCalendar(ffighters):
    calendar = {}
    rejected = {}

    for n in range(1, 18):
        # -- every 2 cycles, readdress priority list
        if (n % 2 == 1):
            recheckPriorities(ffighters)
            clearPriorityModifiers(ffighters)
            # for ffighter in ffighters:
            #     print(ffighter.hire_date, end=" ")
            # print("\n\n")

        # -- then assign time off requests
        for ffighter in ffighters:
            # print(f"{n} : {calendar} \n")
            current_pick = ffighter.picks[n]

            if current_pick is None:
                continue

            # add new date if needed
            if current_pick not in calendar.keys():
                calendar[current_pick] = [ffighter.name]
                continue

            # add to date if possible
            if len(calendar[current_pick]) < 5:
                calendar[current_pick].append(ffighter.name)
                continue

            # mark date as rejected - move up ffighter to top of next priority list
            if ffighter.name not in rejected.keys():
                rejected[ffighter.name] = [current_pick]
            else:
                rejected[ffighter.name].append(current_pick)
            ffighter.priorityModifier = 50
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

            for n, date in enumerate(picks):
                try:
                    picks[n] = datetime.strptime(date, '%m/%d/%Y').date()
                except:
                    picks[n] = None

            hire_date = datetime.strptime(row['HIRE DATE'], '%m/%d/%Y').date()
            ffdata.append(
                FFighter(row['Name'], row['LNAME'], hire_date, picks))
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
    results = toCalendar(ffighters)
    printDictionary(results['calendar'])
    print(results['rejected'])


if __name__ == '__main__':
    main()
