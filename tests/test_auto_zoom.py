"""Unit tests for AutoZoom controller execution with mocked hardware."""

import unittest

from auto_zoom_controller.AutoZoom import AutoZoom
from auto_zoom_controller.DRV8825_Helper import Direction, Stepper
from auto_zoom_controller.gpio_adapter import mock_gpio, set_dry_run


class TestAutoZoom(unittest.TestCase):
    """Test suite for AutoZoom controller operations."""

    def setUp(self):
        set_dry_run(True)
        mock_gpio.reset()

    def tearDown(self):
        mock_gpio.reset()

    def test_initialization(self):
        """Test initial state of AutoZoom instance."""
        zoom = AutoZoom(turns=50)
        self.assertEqual(zoom.turns, 50)
        self.assertEqual(zoom.activations(), 0)
        self.assertEqual(zoom.direction, Direction.backward)
        self.assertEqual(zoom.step_format, Stepper.fullstep)

    def test_job_advances_activation(self):
        """Test calling job() increments activation count and pulses motor."""
        zoom = AutoZoom(turns=5)
        zoom.job()
        self.assertEqual(zoom.activations(), 1)

        zoom.job()
        self.assertEqual(zoom.activations(), 2)

        # Check GPIO outputs were recorded
        output_events = [evt for evt in mock_gpio.history if evt[0] == "output"]
        self.assertTrue(len(output_events) > 0)

    def test_stop_disables_motor(self):
        """Test stop() sets enable pin high (active low disabled)."""
        zoom = AutoZoom(turns=10)
        zoom.stop()
        # Enable pin is pin 12; Stop() sets enable_pin=1
        self.assertEqual(mock_gpio.pin_states.get(12), 1)

    def test_custom_direction_forward(self):
        """Test AutoZoom with forward direction."""
        zoom = AutoZoom(turns=4, direction=Direction.forward, step_format=Stepper.halfstep)
        zoom.job()
        self.assertEqual(zoom.activations(), 1)
        self.assertEqual(mock_gpio.pin_states.get(13), 0)  # DIR pin 0 for forward


if __name__ == "__main__":
    unittest.main()
