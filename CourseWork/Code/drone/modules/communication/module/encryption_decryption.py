import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class EncryptionDecryption:
    """Модуль шифрования/расшифрования [CS]."""

    def __init__(self, state: RobotStatus):
        self._state = state

    def check_compromised(self) -> bool:
        if self._state.hacked:
            self._state.hacked_noticed = True
            return True
        return False
