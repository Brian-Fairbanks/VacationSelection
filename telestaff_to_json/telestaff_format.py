import os
import pandas as pd

# Define paths
input_folder = "telestaff conversion"  # Folder containing shift files
output_file = "telestaff conversion/Telestaff Format.csv"  # Output file path

# Initialize an empty list to store formatted data
formatted_data = []

def format_data(df, shift):
    formatted_rows = []
    current_name_id = ""  # To store the current "Name (ID)"
    
    for _, row in df.iterrows():
        # Check if the row contains a new "Name (ID)" and "Rank"
        if isinstance(row["Name (ID)"], str):
            current_name_id = row["Name (ID)"]  # Update the current "Name (ID)"
        
        # Skip rows without a valid "Date Requested" (i.e., blank spacer rows)
        if pd.isna(row["Date Requested"]):
            continue
        
        # Skip rejected picks
        if row["Determination"] == "Rejected":
            continue
        
        # Extract Payroll ID
        payroll_id = ""
        if isinstance(current_name_id, str):
            id_match = current_name_id.strip().split("ID: ")
            if len(id_match) > 1:
                payroll_id = id_match[1].split(")")[0]  # Get the numeric ID
        
        # Determine Start Time and Duration based on "Increments" value
        if row["Increments"] == "FULL":
            start_time = "7:00:00"
            duration = 24
        elif row["Increments"] == "AM":
            start_time = "7:00:00"
            duration = 12
        elif row["Increments"] == "PM":
            start_time = "19:00:00"
            duration = 12
        else:
            continue  # Skip rows with unknown increments
        
        # Append formatted row
        formatted_rows.append({
            "Payroll ID": payroll_id,
            "Work Code": row["Type"][0] if pd.notna(row["Type"]) else "",  # First letter of "Type"
            "List": "",
            "Start Date": row["Date Requested"],
            "Counts": "",
            "Shift": shift,
            "Start Time": start_time,
            "Duration (hours)": duration,
            "Region": "",  # Required header, leave empty
            "Outcome": "",  # Required header, leave empty
            "Detail Code": "",  # Required header, leave empty
            "Note": ""  # Required header, leave empty
        })
    
    return pd.DataFrame(formatted_rows)


# Process each file in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        file_path = os.path.join(input_folder, filename)
        df = pd.read_csv(file_path)
        
        # Determine the shift from the filename (e.g., -A, -B, -C)
        shift = filename.split('-')[-1].split('.')[0]  # Extract shift
        
        # Format the data and append it
        formatted_df = pd.DataFrame(format_data(df, shift))
        formatted_data.append(formatted_df)

# Concatenate all formatted data
final_df = pd.concat(formatted_data, ignore_index=True)

# Ensure output directory exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Export to CSV
final_df.to_csv(output_file, index=False)

print(f"Formatted data saved to: {output_file}")
