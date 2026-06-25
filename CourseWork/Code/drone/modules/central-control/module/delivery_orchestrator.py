import sys
import time
from pathlib import Path

_ms = Path(__file__).resolve().parents[3] / 'shared'
if str(_ms) not in sys.path:
    sys.path.insert(0, str(_ms))
from import_ms import load_class

GripControl = load_class('central-control', 'grip_control', 'GripControl')
Navigation = load_class('central-control', 'navigation', 'Navigation')
TaskProcessing = load_class('central-control', 'task_processing', 'TaskProcessing')


class DeliveryOrchestrator:
    """Оркестратор процесса доставки [CL]."""

    def __init__(self, robot, communication):
        self._robot = robot
        self._comm = communication
        self._navigation = Navigation(robot)
        self._tasks = TaskProcessing(robot.state)
        self._grip = GripControl(robot)

    def _preflight(self) -> bool:
        if self._robot.battery_check():
            self._tasks.complete('Робот не будет выполнять команду (мало зарядки)')
            return False
        if self._robot.encryption_decryption_module():
            self._tasks.complete('Робот не будет выполнять команду')
            return False
        return True

    def _tick_movement(self, coord, distance):
        self._robot.update_coordinates_qr(coord)
        self._robot.charge_state.drain(1)
        self._robot.update_obstacle_distance(distance)
        diagnosis = self._robot.self_diagnose()
        self._comm.send_telemetry(
            self._robot.id, self._robot.get_status(), diagnosis
        )
        self._comm.publish_alerts_from_status(
            self._robot.id, self._robot.get_status()
        )
        time.sleep(1)

    def move_to_shelf(self, route, distances):
        self._tasks.begin_task()
        self._robot.movement_interrupted = False
        self._robot.stop_charge()
        if not self._preflight():
            return

        self._robot.start_move_shelf()
        for i in range(len(route)):
            if not self._robot.is_move_shelf:
                break
            self._tick_movement(route[i], distances[i])
        self._robot.stop_move_shelf()

        if self._robot.coordinates_qr == route[-1] and not self._robot.movement_interrupted:
            self._tasks.complete('Робот добрался до стеллажа')
        else:
            self._tasks.complete('Робот не добрался до стеллажа')

    def grab_shelf(self):
        self._tasks.begin_task()
        self._tasks.complete(self._grip.grab())

    def move_to_station(self, route, distances):
        self._tasks.begin_task()
        if not self._preflight():
            return

        self._robot.start_move_station()
        for i in range(len(route)):
            if not self._robot.is_move_station:
                break
            self._tick_movement(route[i], distances[i])
        self._robot.stop_move_station()

        if self._robot.coordinates_qr != route[-1] or self._robot.movement_interrupted:
            self._tasks.complete('Не удалось добраться до станции')
        else:
            self._tasks.complete('Робот добрался до станции')

    def drop_shelf(self):
        self._tasks.begin_task()
        self._tasks.complete(self._grip.drop())

    def prepare_shelf_route(self, route_data):
        return self._navigation.prepare_route_to_shelf(route_data)

    def prepare_station_route(self, route_data):
        return self._navigation.prepare_route_to_station(route_data)
