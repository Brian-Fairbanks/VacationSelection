import csv
from datetime import datetime


class FFighter:
    def __init__(self, fname, lname, hire_date, picks):
        self.fname = fname
        self.lname = lname
        self.hire_date = hire_date
        self.picks = picks
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
    n = 1
    for ffighter in arr:
        # print(f"{n} {ffighter.hire_date}")
        # store this seniority order as priority
        ffighter.priority = n
        n += 1
    return arr


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
                print(n)
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
    for ffighter in ffighters:
        print(ffighter)


if __name__ == '__main__':
    main()
