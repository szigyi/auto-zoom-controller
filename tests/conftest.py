"""Pytest configuration and shared test fixtures."""

import pytest

from auto_zoom_controller.gpio_adapter import mock_gpio, set_dry_run


@pytest.fixture(autouse=True)
def ensure_dry_run():
    """Ensure dry-run mock mode is active and clean for every test."""
    set_dry_run(True)
    mock_gpio.reset()
    yield
    mock_gpio.reset()
