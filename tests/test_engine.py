"""Tests for shared mission scheduling and status."""

import threading
import time
import unittest

from auto_zoom_controller.engine import AutoZoomEngine, MissionConfig
from auto_zoom_controller.gpio_adapter import mock_gpio, set_dry_run


class TestAutoZoomEngine(unittest.TestCase):
    def setUp(self):
        set_dry_run(True)
        mock_gpio.reset()

    def tearDown(self):
        mock_gpio.reset()

    def wait_for_state(self, engine, expected_state, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = engine.get_status()
            if status["state"] == expected_state:
                return status
            threading.Event().wait(0.005)
        self.fail(f"engine did not reach {expected_state}: {engine.get_status()}")

    def test_dry_run_completes_and_reports_activations(self):
        engine = AutoZoomEngine()
        config = MissionConfig(
            number_of_total_turns=0,
            interval_in_seconds=0.01,
            length_in_minutes=0.001,
            dry_run=True,
        )

        engine.start(config)
        status = self.wait_for_state(engine, "COMPLETED")

        self.assertEqual(status["total_activations"], 6)
        self.assertEqual(status["activations"], 6)
        self.assertEqual(status["progress"], 1.0)
        self.assertTrue(status["dry_run"])

    def test_stop_interrupts_wait_between_activations(self):
        engine = AutoZoomEngine()
        config = MissionConfig(
            number_of_total_turns=0,
            interval_in_seconds=5,
            length_in_minutes=1,
            dry_run=True,
        )

        engine.start(config)
        self.assertTrue(engine.stop(wait=True))

        status = engine.get_status()
        self.assertEqual(status["state"], "STOPPED")
        self.assertEqual(status["activations"], 0)

    def test_rejects_invalid_mission_config(self):
        engine = AutoZoomEngine()
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            engine.start(MissionConfig(number_of_total_turns=-1))

    def test_rejects_concurrent_mission(self):
        engine = AutoZoomEngine()
        config = MissionConfig(
            number_of_total_turns=0,
            interval_in_seconds=5,
            length_in_minutes=1,
            dry_run=True,
        )

        engine.start(config)
        with self.assertRaisesRegex(RuntimeError, "already running"):
            engine.start(config)
        engine.stop(wait=True)


if __name__ == "__main__":
    unittest.main()
