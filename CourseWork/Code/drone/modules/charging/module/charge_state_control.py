import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class ChargeStateControl:
    """Модуль контроля состояния заряда [SS]."""

    LOW_BATTERY_THRESHOLD = 10

    def __init__(self, state: RobotStatus):
        self._state = state

    def is_low(self) -> bool:
        return self._state.battery_percent < self.LOW_BATTERY_THRESHOLD

    def update_level(self, battery_percent: int):
        self._state.battery_percent = battery_percent
        return f'Уровень заряда робота изменен на {battery_percent} %.'

    def drain(self, amount: int = 1):
        self._state.battery_percent = max(0, self._state.battery_percent - amount)
