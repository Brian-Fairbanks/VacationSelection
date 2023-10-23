import unittest
from loadFile import FFighter, makeCalendar, setPriorities, getData, printFinal, check_rank

# Import your code or modules that need testing


def test_file(file):
    ffighters = setPriorities(getData(file))

    # Note that DICTS, LISTS, and SETS are mutable, and so pass by reference, not pass by value like ints and setPriorities
    # IE, ffighter objects changes

    shiftMembers = list(
        filter(lambda x: x.shift in ["A", "B", "C"], ffighters))
    makeCalendar(shiftMembers, True)
    return shiftMembers


class TestFirefighterScheduling(unittest.TestCase):

    # =================== BCS ====================================

    def test_BCs_1(self):
        # 0 BCs if 3 captains
        results = test_file(".\\Test CSVs\\BCs 1.csv")
        printFinal(results)
        # print(results[0].processed[0].determination)
        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # captain
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # captain
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # captain
        self.assertEqual(
            results[3].processed[0].determination, "Rejected")  # reject BC
        self.assertEqual(results[3].processed[0].reason,
                         "Day already has 0 Battalion Chiefs and 3 Captains off")

    def test_BCs_2(self):
        # 1 BCs if 2 captains
        results = test_file(".\\Test CSVs\\BCs 2.csv")
        printFinal(results)
        # print(results[0].processed[0].determination)
        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # captain
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # captain
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[3].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(results[3].processed[0].reason,
                         "Day already has 1 Battalion Chiefs and 2 Captains off")

    def test_BCs_3(self):
        # 2 BCs if 1 captain
        results = test_file(".\\Test CSVs\\BCs 3.csv")
        printFinal(results)
        # print(results[0].processed[0].determination)
        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # captain
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[3].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(results[3].processed[0].reason,
                         "Day already has 2 Battalion Chiefs and 1 Captains off")

    def test_BCs_4(self):
        # 2 BCs if 0 captain
        results = test_file(".\\Test CSVs\\BCs 4.csv")
        printFinal(results)
        # print(results[0].processed[0].determination)
        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Rejected")  # Reject BC
        self.assertEqual(results[2].processed[0].reason,
                         "Day already has 2 Battalion Chiefs and 0 Captains off")

        # =================== Captains ====================================

    def test_Captains_1(self):
        # 3 captains if 0 BCs
        results = test_file(".\\Test CSVs\\Captains 1.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[3].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[3].processed[0].reason,
                         "Day already has 3 Captains, 0 Lieutenants, and 0 Battalion Chiefs off")

    def test_Captains_2(self):
        # 2 captains if 1 BCs
        results = test_file(".\\Test CSVs\\Captains 2.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[3].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[3].processed[0].reason,
                         "Day already has 2 Captains, 0 Lieutenants, and 1 Battalion Chiefs off")

    def test_Captains_3(self):
        # 1 captains if 2 BCs
        results = test_file(".\\Test CSVs\\Captains 3.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[3].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[3].processed[0].reason,
                         "Day already has 1 Captains, 0 Lieutenants, and 2 Battalion Chiefs off")

    def test_Captains_4(self):
        # 1 captains if 2 BCs and 2 lieutenants
        results = test_file(".\\Test CSVs\\Captains 4.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve lieutenant
        self.assertEqual(
            results[3].processed[0].determination, "Approved")  # Approve lieutenant
        self.assertEqual(
            results[4].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[5].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[5].processed[0].reason,
                         "Day already has 5 members off")

    def test_Captains_5(self):
        # 0 captains if 2 BCs and 3 lieutenants
        results = test_file(".\\Test CSVs\\Captains 5.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve lieutenant
        self.assertEqual(
            results[3].processed[0].determination, "Approved")  # Approve lieutenant
        self.assertEqual(
            results[4].processed[0].determination, "Approved")  # Approve lieutenant
        self.assertEqual(
            results[5].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[5].processed[0].reason,
                         "Day already has 5 members off")

    def test_Same_Day(self):
        # 0 captains if 2 BCs and 3 lieutenants
        results = test_file(".\\Test CSVs\\SameNameSameDay.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # First Day Off
        self.assertEqual(
            results[0].processed[1].determination, "Rejected")  # Reject requesting same day off
        self.assertEqual(results[0].processed[1].reason,
                         "Already requested this day off")

    def test_rank_names_1BC(self):
        # cutoff percent is 0.75

        # Battalion Chief
        self.assertEqual(check_rank("Battle Chef"), "Battalion Chief")  # 0.77
        self.assertEqual(check_rank("battalionchief"), "Battalion Chief")
        # 0.827
        self.assertEqual(check_rank("Bttln Chf"), "Battalion Chief")  # 0.75

    def test_rank_names_2C(self):
        # Captain
        self.assertEqual(check_rank("captin"), "Captain")  # 0.77
        self.assertEqual(check_rank("Cap'in"), "Captain")  # 0.77
        self.assertEqual(check_rank("Captive"), None)  # 0.714

    def test_rank_names_3FF(self):
        # Firefighter
        self.assertEqual(check_rank("fire frightner"), "Firefighter")  # 0.87
        self.assertEqual(check_rank("fitrfightr"), "Firefighter")  # 0.76
        self.assertEqual(check_rank("Fir righter"), "Firefighter")  # 0.81
        self.assertEqual(check_rank("Filewrighter"), "Firefighter")  # 0.78
        self.assertEqual(check_rank("Fireflower"), None)  # 0.67

    def test_rank_names_4PFF(self):
        # Probationary Firefighter
        self.assertEqual(check_rank("probationaryfirefighter"),
                         "Probationary Firefighter")  # 0.89
        self.assertEqual(check_rank("probationaty fire fighter"),
                         "Probationary Firefighter")  # 0.86
        self.assertEqual(check_rank("Profanatory Filerighter"),
                         "Probationary Firefighter")  # 0.77
        self.assertEqual(check_rank("Prbtnry Frfghtr"),
                         "Probationary Firefighter")  # 0.77
        self.assertEqual(check_rank("Proba Firefighter"),
                         "Probationary Firefighter")  # 0.82.  Any less letters will find 'Firefighter' instead

    def test_rank_names_5AS(self):
        # Apparatus Specialist
        self.assertEqual(check_rank("Apprts Spclst"),
                         "Apparatus Specialist")  # 0.78
        self.assertEqual(check_rank("Apparent Speciest"),
                         "Apparatus Specialist")  # 0.76
        self.assertEqual(check_rank("Appartment Specialty"),
                         "Apparatus Specialist")  # 0.75
        self.assertEqual(check_rank("Appathetic Specializations"),
                         None)  # 0.65

    def test_rank_names_6L(self):
        # Lieutenant
        self.assertEqual(check_rank("lieutenants"), "Lieutenant")  # 0.86
        self.assertEqual(check_rank("Leau-tenant"), "Lieutenant")  # 0.86
        self.assertEqual(check_rank("Lute-enant"), "Lieutenant")  # 0.8
        self.assertEqual(check_rank("Lithiumant"), None)  # 0.6
        self.assertEqual(check_rank("Lithuanian"), None)  # 0.5


if __name__ == '__main__':
    unittest.main()
