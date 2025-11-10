# tests/test_firefighter.py
import unittest
from vacation_selection.firefighter import FFighter, Pick
from datetime import datetime, date

class TestFFighter(unittest.TestCase):

    def setUp(self):
        # Create sample picks
        self.picks = [
            Pick(date=date(2024, 10, 20), type="Holiday", increments='AM'),
            Pick(date=date(2024, 10, 21), type="vacation", increments='PM')
        ]
        # Create a sample FFighter instance for testing
        self.ffighter = FFighter(
            idnum=1,
            fname='John',
            lname='Doe',
            hireDate=date(2015, 5, 12),
            rank='Captain',
            shift='A',
            picks=self.picks
        )

    def test_ffighter_initialization(self):
        """Test initialization of FFighter object."""
        self.assertEqual(self.ffighter.name, 'Doe, J')
        self.assertEqual(self.ffighter.rank, 'Captain')

    def test_ffighter_to_dict(self):
        """Test the to_dict() method of FFighter."""
        ffighter_dict = self.ffighter.to_dict()
        self.assertEqual(ffighter_dict['name'], 'Doe, J')
        self.assertEqual(ffighter_dict['rank'], 'Captain')
        self.assertEqual(ffighter_dict['hireDate'], '2015-05-12')

    def test_ffighter_from_dict(self):
        """Test the from_dict() method of FFighter."""
        ffighter_dict = {
            'idnum': 1,
            'fname': 'John',
            'lname': 'Doe',
            'hireDate': '2015-05-12',
            'rank': 'Captain',
            'shift': 'A',
            'approved_days_count': 0,
            'max_days_off': 15,
            'picks': [pick.to_dict() for pick in self.picks],
            'processed': []
        }
        ffighter = FFighter.from_dict(ffighter_dict)
        self.assertEqual(ffighter.name, 'Doe, J')
        self.assertEqual(ffighter.rank, 'Captain')

if __name__ == '__main__':
    unittest.main()
