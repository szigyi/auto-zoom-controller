import logging

from auto_zoom_controller.DRV8825 import DRV8825
from auto_zoom_controller.DRV8825_Helper import Direction, Stepper

logger = logging.getLogger(__name__)


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
        logger.info(
            "Motor activation starting: steps=%d direction=%s step_format=%s",
            self.turns,
            self.turns,
            self.direction,
            self.step_format,
        )
        self.motor.SetMicroStep(Stepper.software, self.step_format)
        self.motor.TurnStep(Dir=self.direction, steps=self.turns, stepdelay=self.step_delay)
        self.motor.Stop()

    def job(self):
        self.__turn()
        self.activated += 1
        logger.info("Activation completed: %d", self.activated)

    def activations(self):
        return self.activated

    def stop(self):
        logger.info("Disabling stepper motor")
        self.motor.Stop()
