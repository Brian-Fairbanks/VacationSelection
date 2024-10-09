import pandas as pd
import random
import datetime

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

# Precompute all eligible days and their shifts between 02/01/2025 and 01/31/2026
start_date = datetime.datetime(2025, 2, 1)
end_date = datetime.datetime(2026, 1, 31)
days_dict = {"A": [], "B": [], "C": []}

current_date = start_date
while current_date <= end_date:
    shift_day_number = (current_date - start_date).days % 3
    if shift_day_number == 0:
        days_dict["A"].append(current_date.strftime("%m/%d/%Y"))
    elif shift_day_number == 1:
        days_dict["B"].append(current_date.strftime("%m/%d/%Y"))
    else:
        days_dict["C"].append(current_date.strftime("%m/%d/%Y"))
    current_date += datetime.timedelta(days=1)

# Function to generate a random person entry
def generate_person(used_ids):
    today = datetime.datetime.now()
    submission_date = today - datetime.timedelta(days=random.randint(0, 21))
    submission_time = submission_date.replace(hour=random.randint(0, 23), minute=random.randint(0, 59), second=random.randint(0, 59))
    if random.random() < 0.3:
        special_name = random.choice(SPECIAL_NAMES)
        first_name, last_name = special_name.split(" ", 1)
    else:
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
    
    # Generate a unique employee ID
    employee_id = 1000
    while employee_id in used_ids:
        employee_id += 1
    used_ids.add(employee_id)
    
    rank = random.choices(
        [
            "Probationary Firefighter", "FireFighter", "Apparatus Specialist",
            "Lieutenant", "Captain", "Battalion Chief"
        ],
        weights=[10, 65, 10, 5, 5, 5],
        k=1
    )[0]
    shift = random.choice(["A", "B", "C"])
    hire_date = today - datetime.timedelta(days=random.randint(0, 365 * 20))
    years_of_service = round((today - hire_date).days / 365, 2)
    acknowledgment = random.choices([
        "I would like to continue with the selection process.",
        "I would prefer to skip the selection, and submit a blank request form."
    ], weights=[.9,.1])

    # If skipping, no shift selections
    days = []
    shifts = []
    num_days = 0
    if "continue" in acknowledgment:
        num_days = random.randint(5, 40)
        available_days = days_dict[shift]
        selected_days = random.sample(available_days, min(num_days, len(available_days)))
        days.extend(selected_days)
        for _ in range(len(selected_days)):
            shifts.append(random.choices(["AM", "PM", "AMPM"], weights=[0.1, 0.1, 0.8], k=1)[0])

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

    return person

# Function to generate a file with a specified number of rows
def generate_file(row_count):
    used_ids = set()
    people = [generate_person(used_ids) for _ in range(row_count)]
    df = pd.DataFrame(people)
    return df

# Function to export the DataFrame to a CSV file
def export_to_CSV(df, filename=None):
    timestamp = datetime.datetime.now().strftime("%m.%d-%H.%M")
    if filename is None:
        filename = f"2025 VACATION REQUEST FORM - Form Responses{timestamp}.csv"
    df.to_csv(filename, index=False)

# Example usage
df = generate_file(50)
export_to_CSV(df, 'random_vacation_requests.csv')