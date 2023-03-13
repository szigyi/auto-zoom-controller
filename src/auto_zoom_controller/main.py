import RPi.GPIO as GPIO
import Logic
from DRV8825 import DRV8825
from DRV8825_Helper import Stepper, Direction
import schedule
import time

from auto_zoom_controller.AutoZoom import AutoZoom


def run(number_of_total_turns, interval_in_seconds, length_of_transition_in_minutes):
    turns = Logic.calculate_number_of_turns(number_of_total_turns, interval_in_seconds, length_of_transition_in_minutes)
    number_of_total_activations = Logic.calculate_number_of_activations(interval_in_seconds, length_of_transition_in_minutes)

    print("Activations: ", number_of_total_activations)
    print("Total Turns: ", number_of_total_turns)
    print("Turns: ", turns)

    try:
        auto_zoom = AutoZoom(turns)
        GPIO.output(12, 0)  # set to low as documentation requires it

        schedule.every(interval_in_seconds).seconds.do(auto_zoom.job)

        while auto_zoom.activations() < number_of_total_activations:
            schedule.run_pending()
            time.sleep(2)

        schedule.clear()
        auto_zoom.stop()
        GPIO.cleanup()
    except Exception as e:
        print("Error {0}".format(str(e.args[0])).encode("utf-8"))
        schedule.clear()
        print("Motor stop")
        auto_zoom.stop()
        GPIO.cleanup()
        exit(1)
    except:
        schedule.clear()
        print("Motor stop")
        auto_zoom.stop()
        GPIO.cleanup()
        exit(1)

    exit(0)


if __name__ == '__main__':
    number_of_total_turns = 27200  # lens specific - 24-240mm Sony G
    interval_in_seconds = 5
    length_of_transition_in_minutes = 10
    run(number_of_total_turns, interval_in_seconds, length_of_transition_in_minutes)
