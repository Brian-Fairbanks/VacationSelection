import os
import json
from read_telestaff_export import read_telestaff_export
import read_supplemental_export as rse
from fuzzywuzzy import fuzz

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
        return []
    json_files.sort(reverse=True)
    json_path = os.path.join(json_folder, json_files[0])
    with open(json_path, 'r') as jf:
        data = json.load(jf)
    print(f"Loaded current JSON file: {json_path}")
    return data

def normalize_text(text):
    """Normalizes text by stripping whitespace and converting to uppercase."""
    return text.strip().upper()

def match_ffighters(new_record, current_data, threshold=80):
    """
    Attempts to match the new_record against current_data.
    First, if an idnum exists, it checks for an exact id match.
    If that fails, it checks for an exact name match.
    Finally, it uses fuzzy matching on the full name (first and last) with the given threshold.
    
    Returns the matching record from current_data if found, otherwise None.
    """
    shift_new = normalize_text(new_record.get("shift", ""))
    new_fname = normalize_text(new_record.get("fname", ""))
    new_lname = normalize_text(new_record.get("lname", ""))
    new_id = str(new_record.get("idnum", "")).strip()

    # Filter candidates by shift.
    candidates = [rec for rec in current_data if normalize_text(rec.get("shift", "")) == shift_new]

    # Primary: If new record has an ID, try to match based on ID.
    if new_id:
        for rec in candidates:
            current_id = str(rec.get("idnum", "")).strip()
            if new_id == current_id and new_id != "":
                print(f"ID match found for ID {new_id} in shift {shift_new}")
                return rec

    # Secondary: Exact name match.
    for rec in candidates:
        cur_fname = normalize_text(rec.get("fname", ""))
        cur_lname = normalize_text(rec.get("lname", ""))
        if new_fname == cur_fname and new_lname == cur_lname:
            print(f"Exact name match found: {new_fname} {new_lname}")
            return rec

    # Tertiary: Fuzzy matching on full names.
    best_match = None
    best_score = 0
    full_name_new = f"{new_fname} {new_lname}"
    for rec in candidates:
        cur_fname = normalize_text(rec.get("fname", ""))
        cur_lname = normalize_text(rec.get("lname", ""))
        full_name_current = f"{cur_fname} {cur_lname}"
        score = fuzz.token_sort_ratio(full_name_new, full_name_current)
        if score > best_score:
            best_score = score
            best_match = rec
    if best_score >= threshold:
        print(f"Fuzzy match: {full_name_new} matched with {normalize_text(best_match.get('fname',''))} {normalize_text(best_match.get('lname',''))} (Score: {best_score})")
        return best_match
    print(f"No match found for {full_name_new} (Best fuzzy score: {best_score})")
    return None

def update_availability(firefighter_entry, operation, day_type, increments, logs, log_message):
    """
    Updates the firefighter's availability based on the operation.
    Computes change (1 for FULL, 0.5 for HALF) and adjusts used days and approved count.
    Logs a warning if used days exceed awarded days.
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

    if day_type == "Vacation":
        awarded = firefighter_entry.get("awarded_vacation_days")
        if awarded is not None and (firefighter_entry.get("used_vacation_days") or 0) > awarded:
            logs.append(f"⚠️ {firefighter_entry['fname']} {firefighter_entry['lname']} exceeded awarded vacation days: used {(firefighter_entry.get('used_vacation_days') or 0)} vs awarded {awarded}.")
    elif day_type == "Holiday":
        awarded = firefighter_entry.get("awarded_holiday_days")
        if awarded is not None and (firefighter_entry.get("used_holiday_days") or 0) > awarded:
            logs.append(f"⚠️ {firefighter_entry['fname']} {firefighter_entry['lname']} exceeded awarded holiday days: used {(firefighter_entry.get('used_holiday_days') or 0)} vs awarded {awarded}.")

def compare_and_update(current_data, new_data):
    """
    Compares and updates JSON firefighter data using new Telestaff exports.
    For each new record, attempts to match using ID (if available) or fuzzy name matching.
    Compares picks by (date, type, determination), ignoring increments.
    
    For JSON firefighters not found in the Telestaff export, their "processed" picks are cleared
    and summary fields are reset to zero.
    
    Returns:
        updated_data: Updated JSON firefighter list (with cleared picks for firefighters not in Telestaff)
        logs: List of log messages
    """
    logs = []
    matched_indices = set()
    added_firefighters = []   # Track new records added from Excel.
    removed_firefighters = [] # Track firefighters cleared from JSON.

    # Process each new record: update matching record or add as new.
    for new_record in new_data:
        match_record = match_ffighters(new_record, current_data)
        if match_record:
            # Found a match; update its processed picks.
            index = current_data.index(match_record)
            matched_indices.add(index)
            json_processed = match_record.get("processed", [])
            telestaff_processed = new_record.get("processed", [])
            json_processed_set = {(entry["date"], entry["type"], entry["determination"]) for entry in json_processed}
            telestaff_processed_set = {(entry["date"], entry["type"], entry["determination"]) for entry in telestaff_processed}

            updated_processed = []

            # Retain picks in JSON that match Telestaff, or are marked as Rejected.
            for entry in json_processed:
                entry_key = (entry["date"], entry["type"], entry["determination"])
                if entry["determination"] == "Rejected":
                    updated_processed.append(entry)
                    logs.append(f"[{new_record['fname']} {new_record['lname']}] {entry['date']} ({entry['type']}) was REJECTED and remains in JSON.")
                elif entry_key in telestaff_processed_set:
                    updated_processed.append(entry)
                    logs.append(f"[{new_record['fname']} {new_record['lname']}] {entry['date']} ({entry['type']}) MATCHED Telestaff data.")
                else:
                    update_availability(
                        match_record,
                        "removal",
                        entry["type"],
                        entry["increments"],
                        logs,
                        f"[{new_record['fname']} {new_record['lname']}] {entry['date']} ({entry['type']}) was REMOVED (not found in Telestaff)."
                    )

            # Add new picks from Telestaff not already in JSON.
            for entry in telestaff_processed:
                entry_key = (entry["date"], entry["type"], entry["determination"])
                if entry_key not in json_processed_set:
                    updated_processed.append(entry)
                    update_availability(
                        match_record,
                        "addition",
                        entry["type"],
                        entry["increments"],
                        logs,
                        f"[{new_record['fname']} {new_record['lname']}] {entry['date']} ({entry['type']}) was ADDED from Telestaff."
                    )

            match_record["processed"] = sorted(updated_processed, key=lambda x: x["date"])

            # Recalculate summary fields.
            approved = 0
            used_vacation = 0
            used_holiday = 0
            for entry in match_record["processed"]:
                if entry["determination"] == "Approved":
                    inc = 1 if entry["increments"].upper() == "FULL" else 0.5
                    approved += inc
                    if entry["type"] == "Vacation":
                        used_vacation += inc
                    elif entry["type"] == "Holiday":
                        used_holiday += inc

            match_record["approved_days_count"] = approved
            match_record["used_vacation_days"] = used_vacation
            match_record["used_holiday_days"] = used_holiday
        else:
            logs.append(f"New entry found in Excel for {new_record['fname']} {new_record['lname']} (ID: {new_record.get('idnum', 'N/A')}); adding to JSON.")
            added_firefighters.append({
                "name": f"{new_record['fname']} {new_record['lname']}",
                "id": new_record.get('idnum', 'N/A'),
                "shift": new_record.get("shift", "Unknown")
            })
            current_data.append(new_record)
            matched_indices.add(len(current_data) - 1)  # Mark the newly added record as matched.

    # For JSON firefighters not found in the Telestaff export,
    # clear all their picks and reset summary fields.
    for idx, rec in enumerate(current_data):
        if idx not in matched_indices:
            rec["processed"] = []
            rec["approved_days_count"] = 0
            rec["used_vacation_days"] = 0
            rec["used_holiday_days"] = 0
            logs.append(f"Cleared all picks for {rec.get('fname','')} {rec.get('lname','')} (ID: {rec.get('idnum','')}) as they were not found in Telestaff export.")
            removed_firefighters.append({
                "name": f"{rec.get('fname','')} {rec.get('lname','')}",
                "id": rec.get('idnum','N/A'),
                "shift": rec.get("shift", "Unknown")
            })

    # Append a verbose summary at the end of logs.
    logs.append("\n========== FINAL SUMMARY ==========")
    logs.append("SUMMARY OF UPDATES:")
    logs.append(f"Total records processed from Telestaff: {len(new_data)}")
    logs.append(f"Total current JSON records: {len(current_data)}\n")
    
    logs.append("NEW FIREFIGHTERS ADDED:")
    if added_firefighters:
        logs.append(f"Count: {len(added_firefighters)}")
        for ff in added_firefighters:
            logs.append(f" - Name: {ff['name']}, ID: {ff['id']}, Shift: {ff['shift']}")
    else:
        logs.append("None")
    
    logs.append("\nFIREFIGHTERS REMOVED (CLEARED):")
    if removed_firefighters:
        logs.append(f"Count: {len(removed_firefighters)}")
        for ff in removed_firefighters:
            logs.append(f" - Name: {ff['name']}, ID: {ff['id']}, Shift: {ff['shift']}")
    else:
        logs.append("None")
    logs.append("===================================\n")

    return current_data, logs

def main():
    json_folder = "./telestaff_to_json/2024_JSON_Place"
    excel_folder = "./telestaff_to_json/raw_telestaff_exports"
    output_folder = "./telestaff_to_json/Output"

    # Input file uses this date (unchanged)
    input_date = "20250318"
    # Output file will use this date in the filename.
    output_date = "2025.03.18"

    shifts = ["A", "B", "C"]

    # Merge new data from all shifts.
    combined_new_data = []
    for shift_type in shifts:
        excel_filename = f"{input_date} - Multiday Roster Report - {shift_type} Shift.xlsx"
        excel_file_path = os.path.join(excel_folder, excel_filename)
        print(f"\nProcessing shift {shift_type} using Excel file: {excel_file_path}")

        try:
            new_data = read_telestaff_export(excel_file_path)
            # Ensure each record has a shift field (if not already present) to help with matching.
            for record in new_data:
                record["shift"] = shift_type
            print(f"Processed {len(new_data)} entries from Excel export for shift {shift_type}.")
            combined_new_data.extend(new_data)
        except Exception as e:
            error_message = f"Error processing Excel file for shift {shift_type}: {e}"
            print(error_message)

    # Merge current JSON data from all shifts.
    combined_current_data = []
    for shift_type in shifts:
        current_data = load_current_json(json_folder, shift_type)
        if current_data:
            combined_current_data.extend(current_data)

    # Perform the update on the combined dataset.
    updated_data, logs = compare_and_update(combined_current_data, combined_new_data)

    # ---- New Lines: Process supplemental export ----
    supplemental_excel_path = "./telestaff_to_json/supplemental_exports/2025 SUPPLEMENTAL VACATION REQUEST FORM - Form Responses.csv"
    hr_excel_path = "./HR_data_plus_ranks.xlsx"  # Provide HR file if needed.
    supplemental_data = rse.read_supplemental_export(supplemental_excel_path, hr_excel_path=hr_excel_path)
    updated_data, supp_logs = rse.append_supplemental_picks(updated_data, supplemental_data)
    logs.extend(supp_logs)
    # ---------------------------------------------------

    os.makedirs(output_folder, exist_ok=True)

    # Write one merged output JSON file.
    updated_json_filename = f"{output_date}-FFighters_merged_ffighters.json"
    updated_json_path = os.path.join(output_folder, updated_json_filename)
    with open(updated_json_path, 'w') as outf:
        json.dump(updated_data, outf, indent=4)
    print(f"\nUpdated merged JSON file written to {updated_json_path}")

    # Write one merged log file.
    log_filename = f"{output_date}-ConversionLog_merged.log"
    log_path = os.path.join(output_folder, log_filename)
    with open(log_path, 'w', encoding='utf-8') as logf:
        for line in logs:
            logf.write(line + "\n")
    print(f"Conversion log written to {log_path}")

if __name__ == "__main__":
    main()
