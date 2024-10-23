import os
import csv

def convert_old_to_new_format(old_file, new_file):
    """
    Converts the old format CSV to the new format by adjusting column names
    and adding the 'Shift Selection' fields, defaulting to 'AMPM' and 'Untyped'.
    """
    with open(old_file, mode='r', encoding='utf-8-sig') as infile, open(new_file, mode='w', newline='', encoding='utf-8-sig') as outfile:
        reader = csv.DictReader(infile)

        # Define new headers
        headers = [
            'Submission Date', 'First Name', 'Last Name', 'Employee ID #', 'Rank', 'Shift',
            'Employee Hire Date', 'Acknowledgment of Form Completion', 'Years of Service'
        ] + [f'Day {i},Shift Selection {i}' for i in range(1, 41)]

        # Flatten headers to match the new format
        flattened_headers = []
        for header in headers:
            flattened_headers.extend(header.split(','))

        writer = csv.DictWriter(outfile, fieldnames=flattened_headers)
        writer.writeheader()

        # Process each row in the old format
        for row in reader:
            new_row = {
                'Submission Date': row['Submission Date'],
                'First Name': row['First Name'],
                'Last Name': row['Last Name'],
                'Employee ID #': row['Employee ID #'],
                'Rank': row['Rank'],
                'Shift': row['Shift'],
                'Employee Hire Date': row['Employee Start Date'],
                'Acknowledgment of Form Completion': 'I would like to continue with the selection process.',
                'Years of Service': row['Years of Service']
            }

            # Map 'Day' and 'Type' columns to new 'Day' and 'Shift Selection' columns
            for i in range(1, 41):
                day_key = f'Day {i}'
                type_key = f'Type {i}' if i != 1 else ' Type'

                if day_key in row and row[day_key]:
                    new_row[f'Day {i}'] = row[day_key]
                    new_row[f'Shift Selection {i}'] = 'AMPM'  # Default to 'AMPM' for all shift selections
                else:
                    new_row[f'Day {i}'] = ''
                    new_row[f'Shift Selection {i}'] = 'AMPM'  # Default to 'AMPM' even if day is missing

            writer.writerow(new_row)

def batch_convert_csvs(src_dir, dest_dir):
    """
    Converts all CSV files in the source directory to the new format and
    saves them in the destination directory.
    """
    # Ensure the destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    # Iterate over all files in the source directory
    for filename in os.listdir(src_dir):
        if filename.endswith('.csv'):
            old_file_path = os.path.join(src_dir, filename)
            new_file_path = os.path.join(dest_dir, filename)

            print(f"Converting: {filename}")
            convert_old_to_new_format(old_file_path, new_file_path)

# Define the source and destination directories
src_dir = 'Test CSVs'
dest_dir = './2025 Test CSVs'

# Run the batch conversion
batch_convert_csvs(src_dir, dest_dir)
