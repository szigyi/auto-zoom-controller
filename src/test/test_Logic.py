from unittest import TestCase

from auto_zoom_controller.Logic import calculate_number_of_turns


class Test(TestCase):
    def test_calculate_number_of_turns(self):
        turns = calculate_number_of_turns(4000, 5, 1)
        self.assertEqual(turns, 333)  # 60 seconds / 5 = 12; 4000 / 12 = 333.33*; round it to int
        self.assertTrue(type(turns) is int)
