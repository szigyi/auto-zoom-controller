"""Unit tests for calculation logic."""

import unittest

from auto_zoom_controller.Logic import (
    calculate_number_of_activations,
    calculate_number_of_turns,
)


class TestLogic(unittest.TestCase):
    """Test suite for calculation logic functions."""

    def test_calculate_number_of_activations_standard(self):
        """Test activations calculation for standard parameters."""
        activations = calculate_number_of_activations(interval_in_seconds=5, length_in_minutes=1)
        self.assertEqual(activations, 12.0)

        activations_10m = calculate_number_of_activations(
            interval_in_seconds=5, length_in_minutes=10
        )
        self.assertEqual(activations_10m, 120.0)

    def test_calculate_number_of_activations_validation(self):
        """Test input validation for non-positive values."""
        with self.assertRaises(ValueError):
            calculate_number_of_activations(interval_in_seconds=0, length_in_minutes=5)

        with self.assertRaises(ValueError):
            calculate_number_of_activations(interval_in_seconds=-1, length_in_minutes=5)

        with self.assertRaises(ValueError):
            calculate_number_of_activations(interval_in_seconds=5, length_in_minutes=0)

        with self.assertRaises(ValueError):
            calculate_number_of_activations(interval_in_seconds=5, length_in_minutes=-10)

    def test_calculate_number_of_turns_legacy(self):
        """Test turn calculation for 4000 total turns over 1 minute with 5s interval."""
        turns = calculate_number_of_turns(
            number_of_total_turns=4000,
            interval_in_seconds=5,
            length_in_minutes=1,
        )
        self.assertEqual(turns, 333)
        self.assertIsInstance(turns, int)

    def test_calculate_number_of_turns_sony_lens(self):
        """Test turn calculation for Sony 24-240mm G (27200 steps, 5s interval, 10 minutes)."""
        turns = calculate_number_of_turns(
            number_of_total_turns=27200,
            interval_in_seconds=5,
            length_in_minutes=10,
        )
        # 10 min * 60s / 5s = 120 activations; 27200 / 120 = 226.666... -> rounds to 227
        self.assertEqual(turns, 227)
        self.assertIsInstance(turns, int)

    def test_calculate_number_of_turns_zero(self):
        """Test zero total steps yields zero turns per activation."""
        turns = calculate_number_of_turns(
            number_of_total_turns=0,
            interval_in_seconds=5,
            length_in_minutes=10,
        )
        self.assertEqual(turns, 0)

    def test_calculate_number_of_turns_negative(self):
        """Test negative step count raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_number_of_turns(
                number_of_total_turns=-100,
                interval_in_seconds=5,
                length_in_minutes=10,
            )


if __name__ == "__main__":
    unittest.main()
