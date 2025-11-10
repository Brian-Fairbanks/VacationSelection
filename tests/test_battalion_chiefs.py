# tests/test_battalion_chiefs.py

import unittest
from tests.test_setup import run_calendar_for_file

class TestBattalionChiefScheduling(unittest.TestCase):
    
    def test_BCs_1(self):
        # 0 BCs if 3 captains
        results, shift_members = run_calendar_for_file('BCs 1.csv')

        # Test assertions based on expected outcomes
        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[3].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(shift_members[3].processed[0].reason,
                         "Increment already has 0 Battalion Chiefs and 3 Captains off")

    def test_BCs_2(self):
        # 1 BC if 2 captains
        results, shift_members = run_calendar_for_file('BCs 2.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(shift_members[3].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(shift_members[3].processed[0].reason,
                         "Increment already has 1 Battalion Chiefs and 2 Captains off")

    def test_BCs_3(self):
        # 2 BCs if 1 captain
        results, shift_members = run_calendar_for_file('BCs 3.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(shift_members[3].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(shift_members[3].processed[0].reason,
                         "Increment already has 2 Battalion Chiefs and 1 Captains off")

    def test_BCs_4(self):
        # 2 BCs if 0 captains
        results, shift_members = run_calendar_for_file('BCs 4.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(shift_members[2].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(shift_members[2].processed[0].reason,
                         "Increment already has 2 Battalion Chiefs and 0 Captains off")


if __name__ == '__main__':
    unittest.main()
