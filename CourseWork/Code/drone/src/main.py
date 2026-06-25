import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DRONE_SHARED = ROOT / 'shared'
if str(DRONE_SHARED) not in sys.path:
    sys.path.insert(0, str(DRONE_SHARED))

_wms = ROOT.parent / 'wms'
if str(_wms) not in sys.path:
    sys.path.insert(0, str(_wms))

from src.ccs import CentralControlSystem
from src.api import create_app

HOST = '0.0.0.0'
PORT = 8000


def main():
    print('=== Запуск drone (разрабатываемая сущность) ===')
    ccs = CentralControlSystem()
    app = create_app(ccs, host=HOST, port=PORT)
    print(f'[SYSTEM] API: http://{HOST}:{PORT}')
    app.run_server()


def start_web():
    threading.Thread(target=main, daemon=False).start()

if __name__ == '__main__':
    main()
