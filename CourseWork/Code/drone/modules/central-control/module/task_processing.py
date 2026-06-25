import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class TaskProcessing:
    """Модуль обработки задания [MM]."""

    def __init__(self, state: RobotStatus):
        self._state = state

    def begin_task(self):
        self._state.task_done = False
        self._state.task_message = None

    def complete(self, message: str):
        self._state.task_message = message
        self._state.task_done = True

    def is_running(self) -> bool:
        return not self._state.task_done
