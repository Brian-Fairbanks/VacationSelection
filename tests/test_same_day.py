# tests/test_same_day.py
import unittest
from tests.test_setup import run_calendar_for_file

class TestSameDayRequests(unittest.TestCase):

    def test_Same_Day(self):
        # Test handling of same-day requests
        results, shift_members = run_calendar_for_file('SameNameSameDay.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # First Day Off
        self.assertEqual(shift_members[0].processed[1].determination, "Rejected")  # Reject same-day request
        self.assertEqual(shift_members[0].processed[1].reason,
                         "Already requested this day off (FULL)")

if __name__ == '__main__':
    unittest.main()
