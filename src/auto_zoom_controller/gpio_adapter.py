"""GPIO hardware adapter with automatic Mock fallback for non-Raspberry Pi environments.

Provides a unified interface whether running on real hardware with RPi.GPIO
or in emulation/dry-run mode on developer workstations and CI runners.
"""

import os
from typing import Any, Union

# Global state to force dry-run / mock mode
_FORCE_DRY_RUN: bool = os.environ.get("AUTO_ZOOM_DRY_RUN", "0") == "1"


class MockGPIO:
    """Mock implementation of RPi.GPIO for dry-run mode and testing."""

    BCM = 11
    BOARD = 10
    OUT = 0
    IN = 1
    HIGH = 1
    LOW = 0

    def __init__(self) -> None:
        self.mode = None
        self.warnings = True
        self.pin_modes: dict[int, int] = {}
        self.pin_states: dict[int, Any] = {}
        self.history: list[tuple[str, Any]] = []

    def setmode(self, mode: int) -> None:
        self.mode = mode
        self.history.append(("setmode", mode))

    def setwarnings(self, flag: bool) -> None:
        self.warnings = flag
        self.history.append(("setwarnings", flag))

    def setup(
        self,
        channels: Union[int, list[int], tuple[int, ...]],
        direction: int,
        initial: Any = None,
    ) -> None:
        if isinstance(channels, (list, tuple)):
            for ch in channels:
                self.pin_modes[ch] = direction
                if initial is not None:
                    self.pin_states[ch] = initial
        else:
            self.pin_modes[channels] = direction
            if initial is not None:
                self.pin_states[channels] = initial
        self.history.append(("setup", (channels, direction, initial)))

    def output(
        self,
        channels: Union[int, list[int], tuple[int, ...]],
        values: Any,
    ) -> None:
        if isinstance(channels, (list, tuple)):
            if isinstance(values, (list, tuple)):
                for ch, val in zip(channels, values):
                    self.pin_states[ch] = val
            else:
                for ch in channels:
                    self.pin_states[ch] = values
        else:
            self.pin_states[channels] = values
        self.history.append(("output", (channels, values)))

    def cleanup(self) -> None:
        self.pin_modes.clear()
        self.pin_states.clear()
        self.mode = None
        self.history.append(("cleanup", None))

    def reset(self) -> None:
        """Clear test history and state."""
        self.history.clear()
        self.pin_modes.clear()
        self.pin_states.clear()
        self.mode = None


_mock_instance = MockGPIO()
_real_gpio = None
_real_gpio_attempted = False


def _get_real_gpio():
    global _real_gpio, _real_gpio_attempted
    if not _real_gpio_attempted:
        _real_gpio_attempted = True
        try:
            import RPi.GPIO as rpi_gpio

            _real_gpio = rpi_gpio
        except (ImportError, RuntimeError):
            _real_gpio = None
    return _real_gpio


def set_dry_run(enabled: bool = True) -> None:
    """Explicitly enable or disable dry-run / mocked GPIO."""
    global _FORCE_DRY_RUN
    _FORCE_DRY_RUN = enabled


def is_dry_run() -> bool:
    """Return True if currently operating with mocked GPIO."""
    if _FORCE_DRY_RUN:
        return True
    return _get_real_gpio() is None


class GPIOProxy:
    """Proxy object forwarding calls to RPi.GPIO or MockGPIO dynamically."""

    BCM = MockGPIO.BCM
    BOARD = MockGPIO.BOARD
    OUT = MockGPIO.OUT
    IN = MockGPIO.IN
    HIGH = MockGPIO.HIGH
    LOW = MockGPIO.LOW

    @property
    def _target(self):
        if is_dry_run():
            return _mock_instance
        real = _get_real_gpio()
        return real if real is not None else _mock_instance

    def setmode(self, mode: int) -> None:
        self._target.setmode(mode)

    def setwarnings(self, flag: bool) -> None:
        self._target.setwarnings(flag)

    def setup(self, *args: Any, **kwargs: Any) -> None:
        self._target.setup(*args, **kwargs)

    def output(self, *args: Any, **kwargs: Any) -> None:
        self._target.output(*args, **kwargs)

    def cleanup(self, *args: Any, **kwargs: Any) -> None:
        self._target.cleanup(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


GPIO = GPIOProxy()
mock_gpio = _mock_instance
