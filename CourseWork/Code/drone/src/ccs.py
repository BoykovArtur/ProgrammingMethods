import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DRONE_SHARED = ROOT / 'shared'
if str(DRONE_SHARED) not in sys.path:
    sys.path.insert(0, str(DRONE_SHARED))

from import_ms import load_class
from src.robot import Robot

DeliveryOrchestrator = load_class(
    'central-control', 'delivery_orchestrator', 'DeliveryOrchestrator'
)
CommunicationModule = load_class(
    'communication', 'communication_module', 'CommunicationModule'
)


class CentralControlSystem:
    """Центральная система управления (сборка модулей drone/modules/)."""

    def __init__(self, communication=None):
        self.communication = communication or CommunicationModule()
        self.robots = self._load_robots()
        self._orchestrators = {
            r.id: DeliveryOrchestrator(r, self.communication, self.robots)
            for r in self.robots
        }

    def _load_robots(self):
        path = ROOT / 'data' / 'robots.json'
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return [Robot(**item) for item in data]

    def robot_by_id(self, robot_id: str):
        for robot in self.robots:
            if str(robot.id).lower() == str(robot_id).lower():
                return robot
        return None

    def orchestrator(self, robot_id: str):
        return self._orchestrators[robot_id]
