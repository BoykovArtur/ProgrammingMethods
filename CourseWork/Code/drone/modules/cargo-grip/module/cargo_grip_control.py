import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class CargoGripControl:
    """Модуль контроля захвата груза [SS]."""

    def __init__(self, state: RobotStatus):
        self._state = state

    def set_weak_grip(self):
        self._state.grab_correctly = False

    def is_secure(self) -> bool:
        return self._state.grab_correctly
