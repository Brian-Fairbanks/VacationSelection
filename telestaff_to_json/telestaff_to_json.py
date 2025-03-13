import os
import json
from read_telestaff_export import read_telestaff_export
from fuzzywuzzy import fuzz, process


def load_current_json(json_folder, shift_type):
    """
    Loads the current JSON file for the given shift type from json_folder.
    Expected filename format: [YYYY.MM.DD]-FFighters-[A,B, or C]_ffighters.json
    Returns the JSON data as a list of dictionaries.
    """
    json_files = [f for f in os.listdir(json_folder) 
                  if f.endswith(f"FFighters-{shift_type}_ffighters.json")]
    if not json_files:
        print(f"No JSON file found for shift type {shift_type} in {json_folder}")
        return None
    
    # Assuming the most recent file (by lexicographic order) is the current one.
    json_files.sort(reverse=True)
    json_path = os.path.join(json_folder, json_files[0])
    with open(json_path, 'r') as jf:
        data = json.load(jf)
    print(f"Loaded current JSON file: {json_path}")
    return data


def create_lookup(data_list):
    """
    Creates a lookup dictionary keyed by (shift, fname, lname).
    Stores all names for fuzzy matching.
    """
    lookup = {}
    all_names = set()  # Store unique name pairs for fuzzy matching

    for entry in data_list:
        if not isinstance(entry, dict):
            continue

        shift = str(entry.get("shift", "")).strip().upper()
        first_name = str(entry.get("fname", "")).strip().upper()
        last_name = str(entry.get("lname", "")).strip().upper()

        # Skip entries with missing names
        if not first_name or not last_name:
            print(f"⚠️ Skipping entry with missing name: {entry}")  # Debugging
            continue  

        all_names.add((first_name, last_name))  # Collect valid names
        key = (shift, first_name, last_name)
        lookup[key] = entry

    print(f"\n📋 Lookup created with {len(all_names)} unique names:")
    print(all_names)  # Debugging

    return lookup, all_names  # Return both lookup and name set for fuzzy matching


def find_best_match(name_tuple, name_list, threshold=80):
    """
    Uses fuzzy matching to find the closest fname/lname pair in `name_list`.
    Converts all names to uppercase before comparison.
    Returns the best match if confidence is above `threshold`, otherwise None.
    """
    first_name, last_name = name_tuple
    query = f"{first_name} {last_name}".upper()

    # Convert all names in the list to uppercase for consistency
    name_list_str = [" ".join(name).upper() for name in name_list]  

    print(f"\n🔍 Searching for match: {query}")  # Debugging

    # Perform fuzzy matching
    best_match = process.extractOne(query, name_list_str, scorer=fuzz.token_sort_ratio)

    if best_match:
        print(f"✅ Best fuzzy match found: {best_match[0]} (Score: {best_match[1]})")  # Debugging
    else:
        print(f"❌ No fuzzy match found for: {query}")

    if best_match and best_match[1] >= threshold:  # Confidence score check
        matched_name = best_match[0].split()
        print(f"🎯 Match Accepted: {matched_name[0]} {matched_name[1]} (Score: {best_match[1]})\n")
        return (matched_name[0], matched_name[1]) if len(matched_name) == 2 else None

    print(f"🚨 Match Rejected: {best_match[0]} (Score: {best_match[1]})\n") if best_match else None
    return None


def match_ffighters(shift, first_name, last_name, current_lookup, current_names):
    """
    Finds the best match for a given shift, first name, and last name.
    First attempts an exact match, then falls back to fuzzy matching.
    
    Returns:
        (json_key, matched_entry) if a match is found, or (None, None) if no match.
    """
    match_key = (shift, first_name, last_name)

    # First, try an exact match
    if match_key in current_lookup:
        print(f"🔹 Exact match found for {first_name} {last_name} in shift {shift}")
        return match_key, current_lookup[match_key]

    # Fallback: Try fuzzy matching
    print(f"🔎 No exact match for {first_name} {last_name} → Trying fuzzy matching...")
    fuzzy_match = find_best_match((first_name, last_name), current_names)

    if fuzzy_match:
        fuzzy_key = (shift, fuzzy_match[0], fuzzy_match[1])
        matched_entry = current_lookup.get(fuzzy_key, None)

        if matched_entry:
            print(f"✅ Fuzzy match success! Matched with {fuzzy_match[0]} {fuzzy_match[1]}")
            return fuzzy_key, matched_entry
        else:
            print(f"❌ Fuzzy match found ({fuzzy_match[0]} {fuzzy_match[1]}) but no corresponding JSON entry exists.")
    else:
        print(f"❌ No fuzzy match found for {first_name} {last_name}")

    return None, None


def dict_list_to_tuples(dict_list):
    """ Converts a list of dictionaries into a sorted list of tuples for comparison. """
    return sorted([tuple(sorted(d.items())) for d in dict_list])


def extract_processed_set(processed_list):
    """ Extracts a set of (date, type, determination) tuples for easy comparison (ignores increments). """
    return {(entry["date"], entry["type"], entry["determination"]) for entry in processed_list}


def update_availability(firefighter_entry, operation, day_type, increments, logs, log_message):
    """
    Updates the firefighter's availability based on the operation.
    
    Parameters:
      firefighter_entry: The JSON record for the firefighter.
      operation: 'addition' for a new Telestaff pick, or 'removal' for a pick removed.
      day_type: The type of day (e.g., "Vacation" or "Holiday").
      increments: The increment value (e.g., "FULL" or "HALF").
      logs: The central log list to append log messages.
      log_message: A message describing the change.
    
    The function computes the change amount (1 for FULL, 0.5 for HALF) and adjusts:
      - used_vacation_days or used_holiday_days (depending on day_type)
      - approved_days_count
    It also checks against awarded days and logs a warning if the used count exceeds the awarded limit.
    """
    change = 1 if increments.upper() == "FULL" else 0.5

    if operation == "addition":
        if day_type == "Vacation":
            firefighter_entry["used_vacation_days"] = (firefighter_entry.get("used_vacation_days") or 0) + change
        elif day_type == "Holiday":
            firefighter_entry["used_holiday_days"] = (firefighter_entry.get("used_holiday_days") or 0) + change
        firefighter_entry["approved_days_count"] = (firefighter_entry.get("approved_days_count") or 0) + change
        logs.append(log_message + " [Addition]")
    elif operation == "removal":
        if day_type == "Vacation":
            firefighter_entry["used_vacation_days"] = (firefighter_entry.get("used_vacation_days") or 0) - change
        elif day_type == "Holiday":
            firefighter_entry["used_holiday_days"] = (firefighter_entry.get("used_holiday_days") or 0) - change
        firefighter_entry["approved_days_count"] = (firefighter_entry.get("approved_days_count") or 0) - change
        logs.append(log_message + " [Removal]")

    # Check awarded vs used days (if awarded info is available)
    if day_type == "Vacation":
        awarded = firefighter_entry.get("awarded_vacation_days")
        if awarded is not None and (firefighter_entry.get("used_vacation_days") or 0) > awarded:
            logs.append(f"⚠️ {firefighter_entry['fname']} {firefighter_entry['lname']} exceeded awarded vacation days: used {(firefighter_entry.get('used_vacation_days') or 0)} vs awarded {awarded}.")
    elif day_type == "Holiday":
        awarded = firefighter_entry.get("awarded_holiday_days")
        if awarded is not None and (firefighter_entry.get("used_holiday_days") or 0) > awarded:
            logs.append(f"⚠️ {firefighter_entry['fname']} {firefighter_entry['lname']} exceeded awarded holiday days: used {(firefighter_entry.get('used_holiday_days') or 0)} vs awarded {awarded}.")


# In compare_and_update, update the tuple comparisons to ignore increments:
def compare_and_update(current_data, new_data):
    """
    Compares and updates JSON firefighter data using new Telestaff exports.
    (Now compares picks by date, type, and determination only, ignoring increments.)
    
    Returns:
       updated_data: Updated JSON firefighter list
       logs: List of log messages
    """
    logs = []
    matched_keys = set()
    
    # Construct lookup tables for JSON and Telestaff data
    current_lookup, current_names = create_lookup(current_data)
    new_lookup, new_names = create_lookup(new_data)

    print(f"\n📋 Total Names in Current JSON: {len(current_names)}")
    print(f"📋 Total Names in New Export: {len(new_names)}")

    for key, new_entry in new_lookup.items():
        shift, fname, lname = key

        json_key, matched_entry = match_ffighters(shift, fname, lname, current_lookup, current_names)

        if matched_entry:
            matched_keys.add(json_key)

            # Use the updated processed set without increments.
            json_processed = matched_entry.get("processed", [])
            telestaff_processed = new_entry.get("processed", [])

            json_processed_set = {(entry["date"], entry["type"], entry["determination"]) for entry in json_processed}
            telestaff_processed_set = {(entry["date"], entry["type"], entry["determination"]) for entry in telestaff_processed}

            updated_processed = []

            # First pass: Process existing JSON picks.
            for entry in json_processed:
                entry_key = (entry["date"], entry["type"], entry["determination"])
                if entry["determination"] == "Rejected":
                    updated_processed.append(entry)
                    logs.append(f"[{fname} {lname}] {entry['date']} ({entry['type']}) was REJECTED and remains in JSON.")
                elif entry_key in telestaff_processed_set:
                    updated_processed.append(entry)
                    logs.append(f"[{fname} {lname}] {entry['date']} ({entry['type']}) MATCHED Telestaff data.")
                else:
                    # Pick removed from Telestaff: update availability and do not add it.
                    update_availability(
                        matched_entry,
                        "removal",
                        entry["type"],
                        entry["increments"],
                        logs,
                        f"[{fname} {lname}] {entry['date']} ({entry['type']}) was REMOVED (not found in Telestaff)."
                    )

            # Second pass: Add new picks from Telestaff that are not in JSON.
            for entry in telestaff_processed:
                entry_key = (entry["date"], entry["type"], entry["determination"])
                if entry_key not in json_processed_set:
                    updated_processed.append(entry)
                    update_availability(
                        matched_entry,
                        "addition",
                        entry["type"],
                        entry["increments"],
                        logs,
                        f"[{fname} {lname}] {entry['date']} ({entry['type']}) was ADDED from Telestaff."
                    )

            matched_entry["processed"] = sorted(updated_processed, key=lambda x: x["date"])

            # Final recalculation of summary fields.
            approved = 0
            used_vacation = 0
            used_holiday = 0
            for entry in matched_entry["processed"]:
                if entry["determination"] == "Approved":
                    inc = 1 if entry["increments"].upper() == "FULL" else 0.5
                    approved += inc
                    if entry["type"] == "Vacation":
                        used_vacation += inc
                    elif entry["type"] == "Holiday":
                        used_holiday += inc

            matched_entry["approved_days_count"] = approved
            matched_entry["used_vacation_days"] = used_vacation
            matched_entry["used_holiday_days"] = used_holiday

            if not matched_entry["processed"]:
                matched_entry["processed"] = json_processed
                logs.append(f"[{fname} {lname}] WARNING: Processed list was empty; restored original JSON picks.")

        else:
            logs.append(f"New entry found in Excel for {key}; adding to JSON.")
            current_data.append(new_entry)

    for key, current_entry in current_lookup.items():
        if key not in matched_keys:
            logs.append(f"Entry in JSON for {key} not found in Excel export.")

    return current_data, logs


def main():
    # Define folder paths.
    json_folder = "./telestaff_to_json/2024_JSON_Place"
    excel_folder = "./telestaff_to_json/raw_telestaff_exports"
    output_folder = "./telestaff_to_json/Output"
    
    # Set the shift type and roster date for naming.
    shift_type = "C"  # Options: "A", "B", or "C"
    roster_date = "20250228"  # New naming convention date portion
    
    # Build Excel file path using the new naming convention.
    excel_filename = f"{roster_date} - Multiday Roster Report - {shift_type} Shift.xlsx"
    excel_file_path = os.path.join(excel_folder, excel_filename)
    
    # Read the new Telestaff export.
    try:
        new_data = read_telestaff_export(excel_file_path)
        print(f"Processed {len(new_data)} entries from Excel export.")
    except Exception as e:
        print("Error processing Excel file:", e)
        return
    
    # Load the current JSON data.
    current_data = load_current_json(json_folder, shift_type)
    if current_data is None:
        return
    
    # Compare and update the current JSON data based on the Excel export.
    updated_data, logs = compare_and_update(current_data, new_data)
    
    # Ensure output directory exists.
    os.makedirs(output_folder, exist_ok=True)
    
    # Write updated JSON file.
    updated_json_path = os.path.join(output_folder, "updated.json")
    with open(updated_json_path, 'w') as outf:
        json.dump(updated_data, outf, indent=4)
    print(f"Updated JSON file written to {updated_json_path}")

    # Write conversion log.
    log_path = os.path.join(output_folder, "conversion.log")
    with open(log_path, 'w', encoding='utf-8') as logf:
        for line in logs:
            logf.write(line + "\n")
    print(f"Conversion log written to {log_path}")


if __name__ == "__main__":
    main()
