from auto_zoom_controller.DRV8825 import DRV8825
from auto_zoom_controller.DRV8825_Helper import Direction, Stepper


class AutoZoom:
    def __init__(
        self,
        turns,
        direction=Direction.backward,
        step_format=Stepper.fullstep,
        step_delay=0.001,
    ):
        self.turns = turns
        self.direction = direction
        self.step_format = step_format
        self.step_delay = step_delay
        self.activated = 0
        self.motor = DRV8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))

    def __turn(self):
        print("Motor turning")
        self.motor.SetMicroStep(Stepper.software, self.step_format)
        self.motor.TurnStep(Dir=self.direction, steps=self.turns, stepdelay=self.step_delay)
        self.motor.Stop()

    def job(self):
        self.__turn()
        self.activated += 1
        print("Activated:", self.activated)

    def activations(self):
        return self.activated

    def stop(self):
        print("Motor stopping")
        self.motor.Stop()
