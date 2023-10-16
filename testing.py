import unittest
from loadFile import FFighter, makeCalendar, setPriorities, getData, printFinal

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
        # 1 captains if 2 BCs and 2 lietenants
        results = test_file(".\\Test CSVs\\Captains 4.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve Lietenant
        self.assertEqual(
            results[3].processed[0].determination, "Approved")  # Approve Lietenant
        self.assertEqual(
            results[4].processed[0].determination, "Approved")  # Approve Captain
        self.assertEqual(
            results[5].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[5].processed[0].reason,
                         "Day already has 5 members off")

    def test_Captains_5(self):
        # 0 captains if 2 BCs and 3 lietenants
        results = test_file(".\\Test CSVs\\Captains 5.csv")
        printFinal(results)

        self.assertEqual(
            results[0].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[1].processed[0].determination, "Approved")  # Approve BC
        self.assertEqual(
            results[2].processed[0].determination, "Approved")  # Approve Lietenant
        self.assertEqual(
            results[3].processed[0].determination, "Approved")  # Approve Lietenant
        self.assertEqual(
            results[4].processed[0].determination, "Approved")  # Approve Lietenant
        self.assertEqual(
            results[5].processed[0].determination, "Rejected")  # Reject Captain
        self.assertEqual(results[5].processed[0].reason,
                         "Day already has 5 members off")


if __name__ == '__main__':
    unittest.main()
