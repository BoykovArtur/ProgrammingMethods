import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class QrValidation:
    """Модуль валидации считывания QR-кода [MS]."""

    INVALID_CODES = frozenset({'Wrong', 'Crossing', 'NotAllowed'})

    def __init__(self, state: RobotStatus):
        self._state = state

    def validate_route(self, route, distances):
        new_route = []
        new_distances = []
        for code, dist in zip(route, distances):
            if code not in self.INVALID_CODES:
                self._state.crossing_noticed = True
                new_route.append(code)
                new_distances.append(dist)
        return new_route, new_distances
