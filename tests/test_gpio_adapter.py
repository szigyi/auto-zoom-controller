"""Unit tests for GPIO adapter and MockGPIO behavior."""

import unittest

from auto_zoom_controller.gpio_adapter import (
    GPIO,
    MockGPIO,
    is_dry_run,
    mock_gpio,
    set_dry_run,
)


class TestGPIOAdapter(unittest.TestCase):
    """Test suite for MockGPIO and GPIO adapter proxy."""

    def setUp(self):
        set_dry_run(True)
        mock_gpio.reset()

    def tearDown(self):
        mock_gpio.reset()

    def test_dry_run_flag(self):
        """Test setting and checking dry-run state."""
        set_dry_run(True)
        self.assertTrue(is_dry_run())

    def test_mock_setup_single_pin(self):
        """Test pin setup with single integer channel."""
        mock = MockGPIO()
        mock.setup(12, MockGPIO.OUT, initial=MockGPIO.LOW)
        self.assertEqual(mock.pin_modes[12], MockGPIO.OUT)
        self.assertEqual(mock.pin_states[12], MockGPIO.LOW)

    def test_mock_setup_multiple_pins(self):
        """Test pin setup with tuple of channels."""
        mock = MockGPIO()
        pins = (16, 17, 20)
        mock.setup(pins, MockGPIO.OUT)
        for pin in pins:
            self.assertEqual(mock.pin_modes[pin], MockGPIO.OUT)

    def test_mock_output_vector(self):
        """Test digital output with tuple values across tuple channels."""
        mock = MockGPIO()
        pins = (16, 17, 20)
        mock.setup(pins, MockGPIO.OUT)
        mock.output(pins, (1, 0, 1))
        self.assertEqual(mock.pin_states[16], 1)
        self.assertEqual(mock.pin_states[17], 0)
        self.assertEqual(mock.pin_states[20], 1)

    def test_gpio_proxy_delegation(self):
        """Test GPIO proxy object delegates properly."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(13, GPIO.OUT)
        GPIO.output(13, GPIO.HIGH)
        self.assertEqual(mock_gpio.pin_states.get(13), GPIO.HIGH)
        GPIO.cleanup()
        self.assertEqual(len(mock_gpio.pin_states), 0)


if __name__ == "__main__":
    unittest.main()
