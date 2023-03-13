import RPi.GPIO as GPIO
import Logic
from datetime import datetime
import time

from auto_zoom_controller.AutoZoom import AutoZoom


def check_time(start_time, interval_in_seconds):
    current_time = datetime.now()
    difference = current_time - start_time
    diff_in_seconds = int(difference.total_seconds())
    return diff_in_seconds % interval_in_seconds == 0


def run(start_time, number_of_total_turns, interval_in_seconds, length_of_transition_in_minutes):
    turns = Logic.calculate_number_of_turns(number_of_total_turns, interval_in_seconds, length_of_transition_in_minutes)
    number_of_total_activations = Logic.calculate_number_of_activations(interval_in_seconds, length_of_transition_in_minutes)

    print("Activations: ", number_of_total_activations)
    print("Total Turns: ", number_of_total_turns)
    print("Turns: ", turns)

    try:
        auto_zoom = AutoZoom(turns)
        GPIO.output(12, 0)  # set to low as documentation requires it

        while auto_zoom.activations() < number_of_total_activations:
            is_it_the_time = check_time(start_time, 5)
            if (is_it_the_time):
                auto_zoom.job()
                time.sleep(2) # let the motor turn and the time pass so no more activation in this second
            time.sleep(0.3)

        auto_zoom.stop()
        GPIO.cleanup()
    except Exception as e:
        print("Error {0}".format(str(e.args[0])).encode("utf-8"))
        print("Motor stop")
        auto_zoom.stop()
        GPIO.cleanup()
        exit(1)
    except:
        print("Motor stop")
        auto_zoom.stop()
        GPIO.cleanup()
        exit(1)

    exit(0)


if __name__ == '__main__':
    number_of_total_turns = 27200  # lens specific - 24-240mm Sony G
    interval_in_seconds = 5
    length_of_transition_in_minutes = 10
    start_time = datetime.now()
    run(start_time, number_of_total_turns, interval_in_seconds, length_of_transition_in_minutes)
