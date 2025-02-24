import json
import csv
from fuzzywuzzy import fuzz

# --- Load JSON Data ---
with open("test.JSON", "r") as json_file:
    data = json.load(json_file)

# --- Load Calendar CSV ---
calendar = {}
with open("calendar.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        date = row["Date"]
        positions = [row[col] for col in reader.fieldnames if col != "Date" and row[col].strip()]
        calendar[date] = positions

# --- Fuzzy Matching Helper ---

def build_match_string(fighter):
    """
    Constructs a string from fighter data to match against the calendar.
    Example: "Jaeger, B - 23" for matching "Jaeger, B - 23 (FULL)".
    """
    return f"{fighter['lname']}, {fighter['fname'][0]} - {fighter['idnum']}"

def get_place(date, fighter):
    """
    For a given date, returns the index of the calendar entry that
    fuzzy matches the fighter's info. Uses a threshold to decide a match.
    Returns None if no good match is found.
    """
    day = calendar.get(date)
    if not day:
        return None
    
    target = build_match_string(fighter)
    for idx, cell in enumerate(day):
        # Check if the target is a substring or fuzzy match exceeds 90.
        if target in cell or fuzz.partial_ratio(target, cell) > 90:
            return idx
    return None

# --- Update Processed Picks ---
for fighter in data:
    for pick in fighter.get("processed", []):
        if pick.get("determination") == "Approved":
            pick["place"] = get_place(pick.get("date"), fighter)
        else:
            pick["place"] = None

# --- Save Updated Data ---
with open("updated_test.json", "w") as outfile:
    json.dump(data, outfile, indent=4)
