"""Shared mission scheduler for the CLI and optional web interface."""

import logging
import math
import threading
import time
from dataclasses import dataclass

from auto_zoom_controller import Logic
from auto_zoom_controller.AutoZoom import AutoZoom
from auto_zoom_controller.DRV8825_Helper import Direction, Stepper
from auto_zoom_controller.gpio_adapter import GPIO, is_dry_run, set_dry_run

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MissionConfig:
    number_of_total_turns: int = 27200
    interval_in_seconds: float = 5.0
    length_in_minutes: float = 10.0
    direction: str = Direction.backward
    step_format: str = Stepper.fullstep
    step_delay: float = 0.001
    dry_run: bool = False

    def validate(self):
        if isinstance(self.number_of_total_turns, bool) or not isinstance(
            self.number_of_total_turns, int
        ):
            raise ValueError("number_of_total_turns must be an integer")
        if self.number_of_total_turns < 0:
            raise ValueError("number_of_total_turns cannot be negative")
        if not math.isfinite(self.interval_in_seconds) or self.interval_in_seconds <= 0:
            raise ValueError("interval_in_seconds must be a finite number greater than 0")
        if not math.isfinite(self.length_in_minutes) or self.length_in_minutes <= 0:
            raise ValueError("length_in_minutes must be a finite number greater than 0")
        if not math.isfinite(self.step_delay) or self.step_delay < 0:
            raise ValueError("step_delay must be a finite non-negative number")
        if self.direction not in (Direction.forward, Direction.backward):
            raise ValueError("direction must be 'forward' or 'backward'")
        step_formats = {
            Stepper.fullstep,
            Stepper.halfstep,
            Stepper.step_1_4,
            Stepper.step_1_8,
            Stepper.step_1_16,
            Stepper.step_1_32,
        }
        if self.step_format not in step_formats:
            raise ValueError("unsupported step_format")


class AutoZoomEngine:
    """Runs one mission at a time and exposes a thread-safe status snapshot."""

    def __init__(self):
        self._condition = threading.Condition()
        self._lock = self._condition
        self._stop_event = threading.Event()
        self._worker = None
        self._state = "IDLE"
        self._config = None
        self._error = None
        self._activations = 0
        self._total_activations = 0
        self._steps_per_activation = 0
        self._started_at = None
        self._paused_at = None

    def start(self, config: MissionConfig):
        config.validate()
        with self._lock:
            if self._state in ("RUNNING", "STOPPING"):
                raise RuntimeError("a mission is already running")

            self._stop_event = threading.Event()
            self._config = config
            self._error = None
            self._activations = 0
            self._total_activations = int(
                Logic.calculate_number_of_activations(
                    config.interval_in_seconds, config.length_in_minutes
                )
            )
            self._steps_per_activation = Logic.calculate_number_of_turns(
                config.number_of_total_turns,
                config.interval_in_seconds,
                config.length_in_minutes,
            )
            self._started_at = time.monotonic()
            self._paused_at = None
            self._state = "RUNNING"
            self._worker = threading.Thread(target=self._run_mission, daemon=True)
            self._worker.start()

        return self.get_status()

    def run(self, config: MissionConfig) -> int:
        """Run synchronously for CLI use while sharing the same mission worker."""
        self.start(config)
        with self._lock:
            worker = self._worker
        try:
            worker.join()
        except KeyboardInterrupt:
            self.stop(wait=True)
            raise

        return 1 if self.get_status()["state"] == "ERROR" else 0

    def stop(self, wait: bool = False) -> bool:
        with self._condition:
            if self._state not in ("RUNNING", "PAUSED"):
                return False
            self._state = "STOPPING"
            self._stop_event.set()
            worker = self._worker
            self._condition.notify_all()

        if wait and worker is not threading.current_thread():
            worker.join()
        return True

    def pause(self) -> bool:
        with self._condition:
            if self._state != "RUNNING":
                return False
            self._paused_at = time.monotonic()
            self._state = "PAUSED"
            self._condition.notify_all()
            return True

    def resume(self) -> bool:
        with self._condition:
            if self._state != "PAUSED":
                return False
            now = time.monotonic()
            self._started_at += now - self._paused_at
            self._paused_at = None
            self._state = "RUNNING"
            self._condition.notify_all()
            return True

    def get_status(self):
        with self._lock:
            now = time.monotonic()
            elapsed = max(0.0, now - self._started_at) if self._started_at is not None else 0.0
            if self._state == "PAUSED" and self._paused_at is not None:
                elapsed = max(0.0, elapsed - (now - self._paused_at))
            next_activation_in = None
            if self._state == "RUNNING" and self._config is not None:
                next_activation_at = self._started_at + (
                    (self._activations + 1) * self._config.interval_in_seconds
                )
                next_activation_in = max(0.0, next_activation_at - now)

            progress = (
                self._activations / self._total_activations if self._total_activations else 0.0
            )
            return {
                "state": self._state,
                "activations": self._activations,
                "total_activations": self._total_activations,
                "steps_per_activation": self._steps_per_activation,
                "progress": progress,
                "elapsed_seconds": elapsed,
                "remaining_seconds": max(
                    0.0,
                    (self._config.length_in_minutes * 60 - elapsed)
                    if self._config is not None
                    else 0.0,
                ),
                "next_activation_in": next_activation_in,
                "dry_run": self._config.dry_run if self._config is not None else True,
                "error": self._error,
            }

    def _run_mission(self):
        auto_zoom = None
        failure = None
        completed = False
        config = self._config
        try:
            set_dry_run(config.dry_run)
            if is_dry_run():
                logger.info("Operating in DRY-RUN mode (GPIO emulation)")

            auto_zoom = AutoZoom(
                turns=self._steps_per_activation,
                direction=config.direction,
                step_format=config.step_format,
                step_delay=config.step_delay,
            )
            GPIO.output(12, 0)

            for activation_index in range(1, self._total_activations + 1):
                while True:
                    with self._condition:
                        if self._stop_event.is_set():
                            break
                        while self._state == "PAUSED" and not self._stop_event.is_set():
                            self._condition.wait()
                        if self._stop_event.is_set():
                            break
                        target_time = self._started_at + (
                            activation_index * config.interval_in_seconds
                        )
                        time_to_wait = max(0.0, target_time - time.monotonic())
                        if time_to_wait == 0:
                            break
                        self._condition.wait(timeout=time_to_wait)
                if self._stop_event.is_set():
                    break

                auto_zoom.job()
                with self._lock:
                    self._activations = activation_index

            completed = not self._stop_event.is_set()
        except Exception as error:
            failure = error
            logger.exception("Mission execution failed")
        finally:
            try:
                if auto_zoom is not None:
                    auto_zoom.stop()
            except Exception as error:
                failure = failure or error
            try:
                GPIO.cleanup()
            except Exception as error:
                failure = failure or error

        with self._lock:
            if failure is not None:
                self._error = str(failure)
                self._state = "ERROR"
            elif completed:
                self._state = "COMPLETED"
                logger.info("Zoom cycle completed successfully")
            else:
                self._state = "STOPPED"
                logger.info("Zoom cycle stopped after %d activations", self._activations)
