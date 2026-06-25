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

EmergencyBraking = load_class('central-control', 'emergency_braking', 'EmergencyBraking')


class SelfDiagnosticModule:
    """Модуль самодиагностики [MM]."""

    def __init__(self, state: RobotStatus, avoidance_threshold: int):
        self._state = state
        self._emergency = EmergencyBraking(state, avoidance_threshold)

    def run(self):
        if self._state.battery_percent <= 10:
            return 'Низкая зарядка батареи'
        return self._emergency.check_obstacles()
