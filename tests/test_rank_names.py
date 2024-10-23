# tests/test_rank_names.py
import unittest
from vacation_selection.validation import check_rank

class TestRankNames(unittest.TestCase):

    def test_rank_names_1BC(self):
        # Battalion Chief
        self.assertEqual(check_rank("Battle Chef"), "Battalion Chief")
        self.assertEqual(check_rank("battalionchief"), "Battalion Chief")
        self.assertEqual(check_rank("Bttln Chf"), "Battalion Chief")

    def test_rank_names_2C(self):
        # Captain
        self.assertEqual(check_rank("captin"), "Captain")
        self.assertEqual(check_rank("Cap'in"), "Captain")
        self.assertEqual(check_rank("Captive"), None)

    def test_rank_names_3FF(self):
        # Firefighter
        self.assertEqual(check_rank("fire frightner"), "Firefighter")
        self.assertEqual(check_rank("fitrfightr"), "Firefighter")
        self.assertEqual(check_rank("Fir righter"), "Firefighter")
        self.assertEqual(check_rank("Filewrighter"), "Firefighter")
        self.assertEqual(check_rank("Fireflower"), None)

    def test_rank_names_4PFF(self):
        # Probationary Firefighter
        self.assertEqual(check_rank("probationaryfirefighter"), "Probationary Firefighter")
        self.assertEqual(check_rank("probationaty fire fighter"), "Probationary Firefighter")
        self.assertEqual(check_rank("Profanatory Filerighter"), "Probationary Firefighter")
        self.assertEqual(check_rank("Prbtnry Frfghtr"), "Probationary Firefighter")
        self.assertEqual(check_rank("Proba Firefighter"), "Probationary Firefighter")

    def test_rank_names_5AS(self):
        # Apparatus Specialist
        self.assertEqual(check_rank("Apprts Spclst"), "Apparatus Specialist")
        self.assertEqual(check_rank("Apparent Speciest"), "Apparatus Specialist")
        self.assertEqual(check_rank("Appartment Specialty"), "Apparatus Specialist")
        self.assertEqual(check_rank("Appathetic Specializations"), None)

    def test_rank_names_6L(self):
        # Lieutenant
        self.assertEqual(check_rank("lieutenants"), "Lieutenant")
        self.assertEqual(check_rank("Leau-tenant"), "Lieutenant")
        self.assertEqual(check_rank("Lute-enant"), "Lieutenant")
        self.assertEqual(check_rank("Lithiumant"), None)
        self.assertEqual(check_rank("Lithuanian"), None)

if __name__ == '__main__':
    unittest.main()
