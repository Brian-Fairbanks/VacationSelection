import pandas as pd
import random
import datetime
import hashlib
import openpyxl
import math

increment_names = ["day_1", "day_2", "day_1day_2"]


# Predefined lists for random name generation
FIRST_NAMES = [
    "Abigail", "Amelia", "Ava", "Benjamin", "Charlotte", "Daniel", 
    "Ella", "Elijah", "Emma", "Evelyn", "Faith", "George", "Harper", 
    "Henry", "Isabella", "James", "Katherine", "Liam", "Logan", 
    "Lucas", "Mason", "Mia", "Noah", "Olivia", "Oliver", "Parker", 
    "Quinn", "Rachel", "Sophia", "Thomas", "Uma", "Victoria", 
    "William", "Xander", "Yara", "Zoe"
]
LAST_NAMES = [
    "Anderson", "Brown", "Clark", "Davis", "Evans", "Foster", 
    "Garcia", "Gonzalez", "Hernandez", "Ingram", "Jackson", 
    "Johnson", "Jones", "King", "Lopez", "Martinez", "Miller", 
    "Nelson", "O'Connor", "Parker", "Quinn", "Rodriguez", 
    "Smith", "Taylor", "Thomas", "Underwood", "Vasquez", 
    "White", "Williams", "Wilson", "Xavier", "Young", "Zoolander"
]

SPECIAL_NAMES = ["Noah Won", "Faye K'Pearson", "Una Reel", "Aibee Fiksean", "Arial Faiknaim", "Anon Ymous"]

# Traditional holidays and surrounding days to weight more heavily
HOLIDAYS = [
    "01/01/2025",  # New Year's Day
    "01/20/2025", "01/19/2025", "01/21/2025",  # Martin Luther King Jr. Day and surrounding days
    "02/17/2025", "02/16/2025", "02/18/2025",  # Presidents' Day and surrounding days
    "05/26/2025", "05/25/2025", "05/27/2025",  # Memorial Day and surrounding days
    "07/04/2025", "07/03/2025", "07/05/2025",  # Independence Day and surrounding days
    "09/01/2025", "08/31/2025", "09/02/2025",  # Labor Day and surrounding days
    "10/13/2025", "10/12/2025", "10/14/2025",  # Columbus Day and surrounding days
    "11/11/2025", "11/10/2025", "11/12/2025",  # Veterans Day and surrounding days
    "11/27/2025", "11/26/2025", "11/28/2025",  # Thanksgiving and surrounding days
    "12/25/2025", "12/24/2025", "12/26/2025",  # Christmas and surrounding days
    "01/01/2026"   # New Year's Day 2026
]

# Precompute all eligible days and their shifts between 02/01/2025 and 01/31/2026
# Starting Feb 4, 2025: shifts are 48 hours (every other day), cycling A->B->C
# Before Feb 4: shifts are 24 hours (daily), cycling A->B->C
start_date = datetime.datetime(2025, 2, 1)
end_date = datetime.datetime(2026, 1, 31)
transition_date = datetime.datetime(2025, 2, 4)  # Date when 48-hour shifts begin
days_dict = {"A": [], "B": [], "C": []}

current_date = start_date
while current_date <= end_date:
    if current_date < transition_date:
        # Before Feb 4: 24-hour shifts (daily rotation)
        shift_day_number = (current_date - start_date).days % 3
    else:
        # After Feb 4: 48-hour shifts (every-other-day rotation)
        # Use (days_diff % 6) // 2 to get 0, 1, or 2
        shift_day_number = ((current_date - transition_date).days % 6) // 2

    formatted_date = current_date.strftime("%m/%d/%Y")
    if shift_day_number == 0:
        days_dict["A"].append(formatted_date)
    elif shift_day_number == 1:
        days_dict["B"].append(formatted_date)
    else:
        days_dict["C"].append(formatted_date)
    current_date += datetime.timedelta(days=1)

# Function to generate a random person entry
def generate_person(used_ids, used_names, available_special_names):
    today = datetime.datetime.now()
    submission_date = today - datetime.timedelta(days=random.randint(0, 21))
    submission_time = submission_date.replace(hour=random.randint(0, 23), minute=random.randint(0, 59), second=random.randint(0, 59))
    
    # Generate unique name
    while True:
        if available_special_names and random.random() < 0.15:
            special_name = random.choice(available_special_names)
            available_special_names.remove(special_name)
            first_name, last_name = special_name.split(" ", 1)
        else:
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
        
        name_hash = hashlib.sha256(f"{first_name} {last_name}".encode()).hexdigest()
        if name_hash not in used_names:
            used_names.add(name_hash)
            break
    
    # Generate a unique employee ID
    employee_id = 1000
    while employee_id in used_ids:
        employee_id += 1
    used_ids.add(employee_id)
    
    hire_date = today - datetime.timedelta(days=random.randint(0, 365 * 20))
    years_of_service = round((today - hire_date).days / 365, 2)
    
    # Determine rank based on years of service
    if years_of_service < 1:
        rank = "Probationary Firefighter"
    else:
        rank = random.choices(
            [
                "FireFighter", "Apparatus Specialist",
                "Lieutenant", "Captain", "Battalion Chief"
            ],
            weights=[65, 10, 5, 5, 5],
            k=1
        )[0]
    
    shift = random.choice(["A", "B", "C"])
    acknowledgment = random.choices([
        "I would like to continue with the selection process.",
        "I would prefer to skip the selection, and submit a blank request form."
    ], weights=[.9, .1])[0]

    # If skipping, no shift selections
    days = []
    shifts = []
    num_days = 0
    if "continue" in acknowledgment:
        num_days = random.randint(5, 40)
        available_days = days_dict[shift]

        # Weight holidays more heavily and allow duplicates
        weighted_days = [day for day in available_days if day in HOLIDAYS] * 2 + available_days
        selected_days = random.choices(weighted_days, k=num_days)

        # Create weighted selection for finalization
        finalized_days = [(day, random.random() * 2.5 if day in HOLIDAYS else random.random()) for day in selected_days]

        # Sort the finalized_days by weight
        finalized_days.sort(key=lambda x: x[1], reverse=True)
        days = [day for day, _ in finalized_days]

        for _ in range(len(days)):
            shifts.append(random.choices(increment_names, weights=[0.1, 0.1, 0.8], k=1)[0])

    # Create the person dictionary
    person = {
        "Submission Date": submission_time.strftime("%m/%d/%Y %H:%M:%S"),
        "First Name": first_name,
        "Last Name": last_name,
        "Employee ID #": employee_id,
        "Rank": rank,
        "Shift": shift,
        "Employee Hire Date": hire_date.strftime("%m/%d/%Y"),
        "Acknowledgment of Form Completion": acknowledgment,
        "Years of Service": years_of_service,
    }

    # Add day and shift selection to the person dictionary
    for i in range(1, num_days + 1):
        person[f"Day {i}"] = days[i - 1] if i <= len(days) else ""
        person[f"Shift Selection {i}"] = shifts[i - 1] if i <= len(shifts) else ""

    # Fill remaining shift selection columns with "AMPM" up to the next multiple of 10
    total_shift_selections = len(shifts)
    next_multiple_of_10 = ((total_shift_selections + 9) // 10) * 10
    for i in range(total_shift_selections + 1, next_multiple_of_10 + 1):
        person[f"Shift Selection {i}"] = "AMPM"

    # Fill remaining day columns with empty strings
    for i in range(num_days + 1, next_multiple_of_10 + 1):
        person[f"Day {i}"] = ""

    floored_years = years_of_service//1
    hr_validation_data = {
        "Department Code": "0400",
        "Employee Number": employee_id,
        "Employee Name": f"{last_name}, {first_name} {random.choice(FIRST_NAMES)} ",
        "Hire Date": hire_date.strftime("%m/%d/%Y"),
        "Years of Service": floored_years,
        "# of Vacation Leave Hours awarded": 192.0 + (24 * (floored_years // 5)),
        "# of Holiday Leave Hours awarded": 144.0
    }

    return person, hr_validation_data  # Return both dictionaries

# Function to generate a file with a specified number of rows
def generate_file(row_count):
    used_ids = set()
    used_names = set()
    available_special_names = SPECIAL_NAMES.copy()
    people = []
    hr_validations = [] 

    for _ in range(row_count):
        person_data, hr_data = generate_person(used_ids, used_names, available_special_names)
        people.append(person_data)
        hr_validations.append(hr_data)

    df = pd.DataFrame(people)
    df_hr = pd.DataFrame(hr_validations)  # Create DataFrame for HR validations
    return df, df_hr


# Function to export the DataFrame to a CSV file
def export_to_CSV(df, filename=None):
    timestamp = datetime.datetime.now().strftime("%m.%d-%H.%M")
    if filename is None:
        filename = f"2025 VACATION REQUEST FORM - Form Responses{timestamp}.csv"
    df.to_csv(filename, index=False)

def export_to_excel(df, filename=None):
    timestamp = datetime.datetime.now().strftime("%m.%d-%H.%M")
    if filename is None:
        filename = f"HR_validations{timestamp}.xlsx"
    
    # Sort the DataFrame before exporting
    df = df.sort_values(by=['Years of Service', 'Employee Name'], ascending=[False, True])
    
    df.to_excel(filename, index=False)

# Example usage
df, df_hr = generate_file(200)  # Generate both DataFrames
export_to_CSV(df, 'random_vacation_requests.csv')
export_to_excel(df_hr, 'HR_validations.xlsx')  # Export HR validations to Excel