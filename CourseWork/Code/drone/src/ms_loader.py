import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRONE_SHARED = ROOT / 'shared'
if str(DRONE_SHARED) not in sys.path:
    sys.path.insert(0, str(DRONE_SHARED))

from import_ms import load_class

__all__ = ['load_class']
