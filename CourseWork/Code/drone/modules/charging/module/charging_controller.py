import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class ChargingController:
    """Контроллер зарядки [MM]."""

    def __init__(self, state: RobotStatus):
        self._state = state

    def start_charge(self):
        if not self._state.is_charging:
            self._state.is_charging = True
            return 'Робот начал заряжаться.'
        return 'Робот уже заряжается.'

    def stop_charge(self):
        if self._state.is_charging:
            self._state.is_charging = False
            return 'Робот прекратил зарядку'
        return 'Робот не заряжается'
