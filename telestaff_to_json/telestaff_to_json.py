# telestaff_to_json.py
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
        - matched_entry (dict): The matched entry from `current_lookup`, or None if no match is found.
    """
    match_key = (shift, first_name, last_name)

    # First, try an exact match
    if match_key in current_lookup:
        print(f"🔹 Exact match found for {first_name} {last_name} in shift {shift}")
        return current_lookup[match_key]

    # Fallback: Try fuzzy matching
    print(f"🔎 No exact match for {first_name} {last_name} → Trying fuzzy matching...")
    fuzzy_match = find_best_match((first_name, last_name), current_names)

    if fuzzy_match:
        match_key = (shift, fuzzy_match[0], fuzzy_match[1])
        matched_entry = current_lookup.get(match_key, None)

        if matched_entry:
            print(f"✅ Fuzzy match success! Matched with {fuzzy_match[0]} {fuzzy_match[1]}")
            return matched_entry
        else:
            print(f"❌ Fuzzy match found ({fuzzy_match[0]} {fuzzy_match[1]}) but no corresponding JSON entry exists.")
    else:
        print(f"❌ No fuzzy match found for {first_name} {last_name}")

    return None

def dict_list_to_tuples(dict_list):
    """ Converts a list of dictionaries into a sorted list of tuples for comparison. """
    return sorted([tuple(sorted(d.items())) for d in dict_list])

def extract_processed_set(processed_list):
    """ Extracts a set of (date, type) tuples for easy comparison. """
    return {(entry["date"], entry["type"]) for entry in processed_list}

def compare_and_update(current_data, new_data):
    """
    Compares and updates JSON firefighter data using new Telestaff exports.

    - Keeps JSON processed picks first.
    - Logs rejected picks, matched picks, removed picks, and new picks.
    - Ensures `processed` is **never completely removed**.

    Returns:
       updated_data: Updated JSON firefighter list
       logs: List of log messages
    """
    logs = []
    
    # Construct lookup tables for JSON and Telestaff data
    current_lookup, current_names = create_lookup(current_data)
    new_lookup, new_names = create_lookup(new_data)

    print(f"\n📋 Total Names in Current JSON: {len(current_names)}")
    print(f"📋 Total Names in New Export: {len(new_names)}")

    for key, new_entry in new_lookup.items():
        shift, fname, lname = key

        matched_entry = match_ffighters(shift, fname, lname, current_lookup, current_names)

        if matched_entry:
            ### Step 1: Extract "Approved" processed dates from both JSON and Telestaff ###
            json_processed = matched_entry.get("processed", [])
            telestaff_processed = new_entry.get("processed", [])

            json_processed_set = {
                (entry["date"], entry["type"], entry["increments"], entry["determination"])
                for entry in json_processed
            }
            telestaff_processed_set = {
                (entry["date"], entry["type"], entry["increments"], entry["determination"])
                for entry in telestaff_processed
            }

            ### Step 2: Build a temporary processed list ###
            updated_processed = []

            # 1️⃣ First Pass: Handle existing JSON data (retain, remove, or log ignored)
            for entry in json_processed:
                entry_tuple = (entry["date"], entry["type"], entry["increments"], entry["determination"])
                
                if entry["determination"] == "Rejected":
                    updated_processed.append(entry)
                    logs.append(f"[{fname} {lname}] {entry['date']} ({entry['type']}) was REJECTED and remains in JSON.")
                
                elif entry_tuple in telestaff_processed_set:
                    updated_processed.append(entry)
                    logs.append(f"[{fname} {lname}] {entry['date']} ({entry['type']}) MATCHED Telestaff data.")

                else:
                    logs.append(f"[{fname} {lname}] {entry['date']} ({entry['type']}) was REMOVED (not found in Telestaff).")

            # 2️⃣ Second Pass: Add new Telestaff data
            for entry in telestaff_processed:
                entry_tuple = (entry["date"], entry["type"], entry["increments"], entry["determination"])
                if entry_tuple not in json_processed_set:
                    updated_processed.append(entry)
                    logs.append(f"[{fname} {lname}] {entry['date']} ({entry['type']}) was ADDED from Telestaff.")

            # 3️⃣ Overwrite the `processed` list with the updated version
            matched_entry["processed"] = sorted(updated_processed, key=lambda x: x["date"])

            ### SAFEGUARD: Ensure `processed` is Not Empty ###
            if not matched_entry["processed"]:
                matched_entry["processed"] = json_processed  # Restore JSON version if empty
                logs.append(f"[{fname} {lname}] WARNING: Processed list was empty; restored original JSON picks.")

        else:
            logs.append(f"New entry found in Excel for {key}; adding to JSON.")
            current_data.append(new_entry)

    ### Step 3: Check for Entries in JSON that No Longer Exist in Telestaff ###
    for key, current_entry in current_lookup.items():
        if key not in new_lookup:
            logs.append(f"Entry in JSON for {key} not found in Excel export.")

    return current_data, logs




def main():
    # Define folder paths.
    json_folder = "./telestaff_to_json/2024_JSON_Place"
    excel_folder = "./telestaff_to_json/raw_telestaff_exports"
    output_folder = "./telestaff_to_json/Output"
    
    # Set the shift type and export date range.
    shift_type = "A"  # Options: "A", "B", or "C"
    export_date_range = "02-01-2025 through 01-31-2026"
    
    # Build Excel file path.
    excel_filename = f"Multiday Roster Report - {shift_type} Shift - {export_date_range}.xlsx"
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
    with open(log_path, 'w') as logf:
        for line in logs:
            logf.write(line + "\n")
    print(f"Conversion log written to {log_path}")


if __name__ == "__main__":
    main()
