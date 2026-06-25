import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class Manipulators:
    """Манипуляторы [MM]."""

    def __init__(self, state: RobotStatus):
        self._state = state

    def grab(self):
        self._state.grab_correctly = True
        if not self._state.take_shelf:
            self._state.take_shelf = True
            return 'Робот закрепил стеллаж'
        return 'Робот уже держит стеллаж'

    def drop(self):
        if self._state.take_shelf and self._state.grab_correctly:
            self._state.take_shelf = False
            return 'Робот отпустил стеллаж'
        if not self._state.grab_correctly:
            self._state.grab_correctly = True
            return 'Робот закрепил стеллаж'
        return 'Робот не держит стеллаж'
