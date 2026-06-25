class GripControl:
    """Модуль управления захватом [CM]."""

    def __init__(self, robot):
        self._robot = robot

    def grab(self):
        return self._robot.manipulators.grab()

    def drop(self):
        return self._robot.manipulators.drop()
