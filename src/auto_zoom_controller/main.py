import RPi.GPIO as GPIO
import Logic
from DRV8825 import DRV8825
from DRV8825_Helper import Stepper, Direction
import schedule
import time

from auto_zoom_controller.AutoZoom import AutoZoom


def run(interval_in_seconds, length_in_minutes):
    number_of_total_turns = 4000  # lens specific
    turns = Logic.calculate_number_of_turns(number_of_total_turns, interval_in_seconds, length_in_minutes)
    number_of_total_activations = Logic.calculate_number_of_activations(interval_in_seconds, length_in_minutes)
    activated = 0

    print("Activations: ", number_of_total_activations)
    print("Total Turns: ", number_of_total_turns)
    print("Turns: ", turns)

    try:
        auto_zoom = AutoZoom(turns)
        GPIO.output(12, 0)  # set to low as documentation requires it

        schedule.every(interval_in_seconds).seconds.do(auto_zoom.job)

        while activated <= number_of_total_activations:
            schedule.run_pending()
            time.sleep(1)

        schedule.clear()
        auto_zoom.stop()
        GPIO.cleanup()
        exit()
    except Exception as e:
        print("Error {0}".format(str(e.args[0])).encode("utf-8"))
        schedule.clear()
        print("\nMotor stop")
        auto_zoom.stop()
        GPIO.cleanup()
        exit()
    except:
        schedule.clear()
        print("\nMotor stop")
        auto_zoom.stop()
        GPIO.cleanup()
        exit()


if __name__ == '__main__':
    interval_in_seconds = 5
    length_in_minutes = 5
    run(interval_in_seconds, length_in_minutes)
