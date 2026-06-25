import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus

import sys
from pathlib import Path
_ms = Path(__file__).resolve().parents[3] / 'shared'
if str(_ms) not in sys.path:
    sys.path.insert(0, str(_ms))
from import_ms import load_class

MovementSystem = load_class('movement', 'movement_system', 'MovementSystem')


class EmergencyBraking:
    """Модуль аварийного торможения [MM]."""

    def __init__(self, state: RobotStatus, avoidance_threshold: int):
        self._state = state
        self._threshold = avoidance_threshold
        self._movement = MovementSystem(state)

    def check_obstacles(self):
        if (
            self._state.is_move_shelf
            and self._state.obstacle_distance < self._threshold
        ):
            self._movement.emergency_stop_all()
            self._state.is_move_shelf = False
            return (
                'Расстояние до препятствия меньше безопасного значения. '
                'Невозможно добраться до стеллажа'
            )
        if (
            self._state.is_move_station
            and self._state.obstacle_distance < self._threshold
        ):
            self._movement.emergency_stop_all()
            self._state.is_move_station = False
            return (
                'Расстояние до препятствия меньше безопасного значения. '
                'Невозможно добраться до станции'
            )
        if (
            self._state.is_move_back
            and self._state.obstacle_distance < self._threshold
        ):
            self._movement.emergency_stop_all()
            self._state.is_move_back = False
            return (
                'Расстояние до препятствия меньше безопасного значения. '
                'Невозможно вернуть стеллаж'
            )
        if (
            self._state.is_move_home
            and self._state.obstacle_distance < self._threshold
        ):
            self._movement.emergency_stop_all()
            self._state.is_move_home = False
            return (
                'Расстояние до препятствия меньше безопасного значения. '
                'Невозможно вернуться на базу'
            )
        return None
