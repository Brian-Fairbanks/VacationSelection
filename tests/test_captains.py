# tests/test_captains.py
import unittest
from tests.test_setup import run_calendar_for_file

class TestCaptainScheduling(unittest.TestCase):

    def test_Captains_1(self):
        # 3 captains if 0 BCs
        results, shift_members = run_calendar_for_file('captains 1.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[3].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(shift_members[3].processed[0].reason,
                         "Increment already has 3 Captains, 0 Lieutenants, and 0 Battalion Chiefs off")

    def test_Captains_2(self):
        # 2 captains if 1 BC
        results, shift_members = run_calendar_for_file('captains 2.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[3].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(shift_members[3].processed[0].reason,
                         "Increment already has 2 Captains, 0 Lieutenants, and 1 Battalion Chiefs off")

    def test_Captains_3(self):
        # 1 captain if 2 BCs
        results, shift_members = run_calendar_for_file('captains 3.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[3].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(shift_members[3].processed[0].reason,
                         "Increment already has 1 Captains, 0 Lieutenants, and 2 Battalion Chiefs off")

    def test_Captains_4(self):
        # 1 captain if 2 BCs and 2 lieutenants
        results, shift_members = run_calendar_for_file('captains 4.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Lieutenant
        self.assertEqual(shift_members[3].processed[0].determination, "Approved")  # Lieutenant
        self.assertEqual(shift_members[4].processed[0].determination, "Approved")  # Captain
        self.assertEqual(shift_members[5].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(shift_members[5].processed[0].reason,
                         "Day already has maximum firefighters off")

    def test_Captains_5(self):
        # 0 captains if 2 BCs and 3 lieutenants
        results, shift_members = run_calendar_for_file('captains 5.csv')

        self.assertEqual(shift_members[0].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[1].processed[0].determination, "Approved")  # BC
        self.assertEqual(shift_members[2].processed[0].determination, "Approved")  # Lieutenant
        self.assertEqual(shift_members[3].processed[0].determination, "Approved")  # Lieutenant
        self.assertEqual(shift_members[4].processed[0].determination, "Approved")  # Lieutenant
        self.assertEqual(shift_members[5].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(shift_members[5].processed[0].reason,
                         "Day already has maximum firefighters off")


if __name__ == '__main__':
    unittest.main()
