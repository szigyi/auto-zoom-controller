"""Unit tests for command-line interface argument parsing."""

import subprocess
import sys
import unittest

from auto_zoom_controller.DRV8825_Helper import Direction, Stepper
from auto_zoom_controller.main import DIRECTION_MAP, create_parser, main


class TestCLI(unittest.TestCase):
    """Test suite for CLI arguments and parser configuration."""

    def setUp(self):
        self.parser = create_parser()

    def test_default_arguments(self):
        """Test default arguments match calibrated setup."""
        args = self.parser.parse_args([])
        self.assertEqual(args.interval_in_seconds, 5.0)
        self.assertEqual(args.length_in_minutes, 10.0)
        self.assertEqual(args.number_of_total_turns, 27200)
        self.assertEqual(args.direction, "in")
        self.assertEqual(args.step_format, Stepper.fullstep)
        self.assertEqual(args.step_delay, 0.001)
        self.assertFalse(args.dry_run)
        self.assertFalse(args.verbose)

    def test_custom_arguments(self):
        """Test parsing user-supplied flags."""
        argv = [
            "-i",
            "2.5",
            "-d",
            "1.5",
            "-s",
            "5000",
            "--direction",
            "out",
            "--step-format",
            Stepper.halfstep,
            "--step-delay",
            "0.002",
            "--dry-run",
            "--verbose",
        ]
        args = self.parser.parse_args(argv)
        self.assertEqual(args.interval_in_seconds, 2.5)
        self.assertEqual(args.length_in_minutes, 1.5)
        self.assertEqual(args.number_of_total_turns, 5000)
        self.assertEqual(args.direction, "out")
        self.assertEqual(args.step_format, "halfstep")
        self.assertEqual(args.step_delay, 0.002)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.verbose)

    def test_direction_mapping(self):
        """Test direction string mappings to internal Direction constants."""
        self.assertEqual(DIRECTION_MAP["in"], Direction.backward)
        self.assertEqual(DIRECTION_MAP["backward"], Direction.backward)
        self.assertEqual(DIRECTION_MAP["out"], Direction.forward)
        self.assertEqual(DIRECTION_MAP["forward"], Direction.forward)

    def test_invalid_direction(self):
        """Test invalid direction option triggers parser error."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--direction", "sideways"])

    def test_invalid_step_format(self):
        """Test invalid step format triggers parser error."""
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["--step-format", "microstep99"])

    def test_main_dry_run_execution(self):
        """Test executing main() with dry-run parameters."""
        ret = main(["--dry-run", "-i", "0.05", "-d", "0.002", "-s", "10"])
        self.assertEqual(ret, 0)

    def test_cli_logs_include_timestamps_and_verbose_driver_details(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "auto_zoom_controller.main",
                "--dry-run",
                "--verbose",
                "--interval",
                "0.01",
                "--duration",
                "0.001",
                "--steps",
                "0",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        timestamp = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        self.assertRegex(
            result.stderr,
            rf"(?m)^{timestamp} INFO __main__: Starting zoom mission:",
        )
        self.assertRegex(
            result.stderr,
            rf"(?m)^{timestamp} INFO auto_zoom_controller\.DRV8825: Microstep control mode:",
        )


if __name__ == "__main__":
    unittest.main()
