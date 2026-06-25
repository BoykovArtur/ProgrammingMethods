from pathlib import Path
import sys

_IDL = Path(__file__).resolve().parent
if str(_IDL) not in sys.path:
    sys.path.insert(0, str(_IDL))

from robot_status import RobotStatus, RouteSegment

__all__ = ['RobotStatus', 'RouteSegment']
