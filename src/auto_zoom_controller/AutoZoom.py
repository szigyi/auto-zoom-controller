from DRV8825 import DRV8825
from DRV8825_Helper import Stepper, Direction


class AutoZoom:

    def __init__(self, turns):
        self.turns = turns
        self.activated = 0
        self.motor = DRV8825(dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))

    def __turn(self):
        print("Motor turning")
        self.motor.SetMicroStep(Stepper.software, Stepper.fullstep)
        self.motor.TurnStep(Dir=Direction.backward, steps=self.turns, stepdelay=0.001)
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
