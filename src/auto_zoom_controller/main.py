"""Main entry point and CLI for auto-zoom-controller.

Uses absolute drift-free timing for predictable, precise intervalometer activations.
"""

import argparse
import sys
import time
from datetime import datetime
from importlib import metadata

from auto_zoom_controller import Logic
from auto_zoom_controller.AutoZoom import AutoZoom
from auto_zoom_controller.DRV8825_Helper import Direction, Stepper
from auto_zoom_controller.gpio_adapter import GPIO, is_dry_run, set_dry_run

DIRECTION_MAP = {
    "in": Direction.backward,
    "backward": Direction.backward,
    "out": Direction.forward,
    "forward": Direction.forward,
}


def get_version() -> str:
    """Retrieve package version or fallback."""
    try:
        return metadata.version("auto-zoom-controller")
    except metadata.PackageNotFoundError:
        return "0.1.0-dev"


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="auto-zoom",
        description="Automated lens zoom controller for timelapse photography using a Raspberry Pi.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        dest="interval_in_seconds",
        type=float,
        default=5.0,
        help="Interval between activations in seconds (default: 5.0)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        dest="length_in_minutes",
        type=float,
        default=10.0,
        help="Total duration of zoom transition in minutes (default: 10.0)",
    )
    parser.add_argument(
        "-s",
        "--steps",
        dest="number_of_total_turns",
        type=int,
        default=27200,
        help="Total motor steps for full zoom throw (default: 27200, Sony 24-240mm G)",
    )
    parser.add_argument(
        "--direction",
        choices=["in", "out", "backward", "forward"],
        default="in",
        help="Zoom direction: 'in'/'backward' or 'out'/'forward' (default: in)",
    )
    parser.add_argument(
        "--step-format",
        choices=[
            Stepper.fullstep,
            Stepper.halfstep,
            Stepper.step_1_4,
            Stepper.step_1_8,
            Stepper.step_1_16,
            Stepper.step_1_32,
        ],
        default=Stepper.fullstep,
        help="Microstepping format (default: fullstep)",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.001,
        help="Delay between step pulses in seconds (default: 0.001)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Emulate motor execution without sending hardware GPIO signals",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    return parser


def run(
    number_of_total_turns: int = 27200,
    interval_in_seconds: float = 5.0,
    length_in_minutes: float = 10.0,
    direction: str = Direction.backward,
    step_format: str = Stepper.fullstep,
    step_delay: float = 0.001,
    dry_run: bool = False,
    start_time: datetime = None,
) -> int:
    """Execute the automated zoom controller loop using drift-free absolute timing."""
    if dry_run:
        set_dry_run(True)

    if is_dry_run():
        print("[INFO] Operating in DRY-RUN mode (GPIO emulation).")

    if start_time is None:
        start_time = datetime.now()

    start_monotonic = time.monotonic()

    turns = Logic.calculate_number_of_turns(
        number_of_total_turns, interval_in_seconds, length_in_minutes
    )
    number_of_total_activations = int(
        Logic.calculate_number_of_activations(interval_in_seconds, length_in_minutes)
    )

    print("========================================")
    print("Auto Zoom Controller Configuration:")
    print(f"  Start Time:         {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration:           {length_in_minutes} min")
    print(f"  Interval:           {interval_in_seconds} sec")
    print(f"  Total Activations:  {number_of_total_activations}")
    print(f"  Total Steps:        {number_of_total_turns}")
    print(f"  Steps per Turn:     {turns}")
    print(f"  Direction:          {direction}")
    print(f"  Microstep Format:   {step_format}")
    print("========================================")

    auto_zoom = None
    try:
        auto_zoom = AutoZoom(
            turns=turns,
            direction=direction,
            step_format=step_format,
            step_delay=step_delay,
        )
        GPIO.output(12, 0)  # enable pin active low

        # Drift-free absolute scheduling loop
        for activation_index in range(1, number_of_total_activations + 1):
            target_time = start_monotonic + (activation_index * interval_in_seconds)
            time_to_wait = target_time - time.monotonic()

            while time_to_wait > 0:
                # Sleep in short increments to remain responsive to user interruption
                sleep_slice = min(time_to_wait, 0.25)
                time.sleep(sleep_slice)
                time_to_wait = target_time - time.monotonic()

            auto_zoom.job()

        print("[INFO] Zoom cycle completed successfully.")
        return 0
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user (Ctrl+C).")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1
    finally:
        if auto_zoom is not None:
            auto_zoom.stop()
        GPIO.cleanup()


def main(argv=None) -> int:
    """CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args(argv)

    resolved_direction = DIRECTION_MAP.get(args.direction, Direction.backward)

    return run(
        number_of_total_turns=args.number_of_total_turns,
        interval_in_seconds=args.interval_in_seconds,
        length_in_minutes=args.length_in_minutes,
        direction=resolved_direction,
        step_format=args.step_format,
        step_delay=args.step_delay,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
