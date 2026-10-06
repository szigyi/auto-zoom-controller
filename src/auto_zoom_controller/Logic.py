"""Calculation logic for lens zoom turns and intervalometer activations."""


def calculate_number_of_activations(interval_in_seconds: float, length_in_minutes: float) -> float:
    """Calculate the total number of activations over the given duration.

    :param interval_in_seconds: Time interval between activations in seconds.
    :param length_in_minutes: Total shoot duration in minutes.
    :return: Total expected activations.
    """
    if interval_in_seconds <= 0:
        raise ValueError("interval_in_seconds must be greater than 0")
    if length_in_minutes <= 0:
        raise ValueError("length_in_minutes must be greater than 0")

    length_in_seconds = length_in_minutes * 60
    return length_in_seconds / interval_in_seconds


def calculate_number_of_turns(
    number_of_total_turns: int,
    interval_in_seconds: float,
    length_in_minutes: float,
) -> int:
    """Calculate the number of motor steps per activation.

    :param number_of_total_turns: Total motor steps required for the full zoom throw.
    :param interval_in_seconds: Time interval between activations in seconds.
    :param length_in_minutes: Total shoot duration in minutes.
    :return: Motor steps per activation, rounded to nearest integer.
    """
    if number_of_total_turns < 0:
        raise ValueError("number_of_total_turns cannot be negative")

    number_of_activations = calculate_number_of_activations(interval_in_seconds, length_in_minutes)
    if number_of_activations == 0:
        return 0

    return int(round(number_of_total_turns / number_of_activations, 0))
