import unittest
import os
from datetime import datetime, date
from vacation_selection.file_io import (
    write_ffighters_to_json,
    read_ffighters_from_json,
    write_picks_to_csv
)
from vacation_selection.firefighter import FFighter, Pick

class TestFileIO(unittest.TestCase):

    def setUp(self):
        """Set up test data and file paths."""
        self.test_ffighters = [
            FFighter(
                idnum=1,
                fname='John',
                lname='Doe',
                hireDate=date(2015, 5, 12),
                rank='Captain',
                shift='A',
                picks=[
                    Pick(date=date(2024, 10, 20), type="Holiday", increments='AM'),
                    Pick(date=date(2024, 10, 21), type="Vacation", increments='PM')
                ]
            )
        ]
        # Use a temporary directory within the project directory for testing
        self.test_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(self.test_dir, exist_ok=True)

        self.json_file_path = os.path.join(self.test_dir, '2024-10-21-FFighters-TestResults.json')
        self.csv_file_path = os.path.join(self.test_dir, '2024-10-21-FFighters-TestResults.csv')
        self.runtime = '2024-10-21'
        self.suffix = 'TestResults'

    def test_write_ffighters_to_json(self):
        """Test writing firefighter data to a JSON file."""
        write_ffighters_to_json(self.test_ffighters, self.suffix, self.test_dir, self.runtime)
        # Check if the file was created
        self.assertTrue(os.path.exists(self.json_file_path))

    def test_read_ffighters_from_json(self):
        """Test reading firefighter data from a JSON file."""
        # Write to JSON first
        write_ffighters_to_json(self.test_ffighters, self.suffix, self.test_dir, self.runtime)
        # Read back from JSON
        ffighters = read_ffighters_from_json(self.json_file_path)
        # Check the number of firefighters read
        self.assertEqual(len(ffighters), len(self.test_ffighters))
        # Check the details of the first firefighter
        self.assertEqual(ffighters[0].name, self.test_ffighters[0].name)
        self.assertEqual(ffighters[0].rank, self.test_ffighters[0].rank)

    def test_write_picks_to_csv(self):
        """Test writing firefighter picks to a CSV file."""
        write_picks_to_csv(self.test_ffighters, self.suffix, self.test_dir, self.runtime)
        # Check if the file was created
        self.assertTrue(os.path.exists(self.csv_file_path))

        # Read back the CSV and check its content
        with open(self.csv_file_path, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 0)  # Check that lines were written
            self.assertIn('Name,Rank,Date Requested,Type,Increments,Determination,Reason\n', lines[0])

    def tearDown(self):
        """Clean up the generated test files."""
        if os.path.exists(self.json_file_path):
            os.remove(self.json_file_path)
        if os.path.exists(self.csv_file_path):
            os.remove(self.csv_file_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

if __name__ == '__main__':
    unittest.main()
