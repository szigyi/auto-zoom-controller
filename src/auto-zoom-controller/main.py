import RPi.GPIO as GPIO
import Logic
from DRV8825 import DRV8825
from DRV8825_Helper import Stepper, Direction
import schedule
import time


def __turn(motor, turns):
    motor.SetMicroStep(Stepper.softward, Stepper.fullstep)
    motor.TurnStep(Dir=Direction.forward, steps=turns, stepdelay=0.001)
    motor.Stop()


def run(interval_in_seconds, length_in_minutes):
    number_of_total_turns = 4000  # lens specific
    turns = Logic.calculate_number_of_turns(number_of_total_turns, interval_in_seconds, length_in_minutes)
    number_of_total_activations = Logic.calculate_number_of_activations(interval_in_seconds, length_in_minutes)
    activated = 0

    print("Activations: ", number_of_total_activations)
    print("Total Turns: ", number_of_total_turns)
    print("Turns: ", turns)

    try:
        motor = DRV8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
        GPIO.output(12, 0)  # set to low as documentation requires it

        def job():
            nonlocal activated
            __turn(motor, turns)
            activated += 1

        schedule.every(interval_in_seconds).seconds.do(job)

        while number_of_total_activations <= activated:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        print("Error {0}".format(str(e.args[0])).encode("utf-8"))
        schedule.clear()
        print("\nMotor stop")
        motor.Stop()
        GPIO.cleanup()
        exit()


if __name__ == '__main__':
    interval_in_seconds = 5
    length_in_minutes = 10
    run(interval_in_seconds, length_in_minutes)
