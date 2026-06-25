import sys
from pathlib import Path

CROSSING = 'Crossing'


def _get_wms():
    wms_path = Path(__file__).resolve().parents[3].parent / 'wms'
    if str(wms_path) not in sys.path:
        sys.path.insert(0, str(wms_path))
    from wms import wms
    return wms


class DeliveryOrchestrator:
    """Оркестратор доставки — координирует подсистемы робота."""

    def __init__(self, robot, communication, all_robots=None):
        self.robot = robot
        self.communication = communication
        self.all_robots = all_robots or []
        self._wms = _get_wms()

    def prepare_shelf_route(self, route_data):
        return (
            list(route_data.get('route_to_shelf', [])),
            list(route_data.get('distances_to_shelf', [])),
        )

    def prepare_station_route(self, route_data):
        return (
            list(route_data.get('route_to_station', [])),
            list(route_data.get('distances_to_station', [])),
        )

    def _reset_task(self):
        self.robot.task_done = False
        self.robot.task_message = None
        self.robot.movement_interrupted = False

    def _update_wms_route(self, route_key, dist_key, route, distances):
        self._wms.routes.setdefault(self.robot.id, {})
        self._wms.routes[self.robot.id][route_key] = route
        self._wms.routes[self.robot.id][dist_key] = distances

    def _check_crossing(self, coord):
        if coord != CROSSING:
            return False
        for other in self.all_robots:
            if other.id == self.robot.id:
                continue
            if other.coordinates_qr == CROSSING:
                self.robot.crossing_noticed = True
                return True
            other_data = self._wms.routes.get(other.id, {})
            if CROSSING in other_data.get('route_to_shelf', []):
                self.robot.crossing_noticed = True
                return True
        return False

    def _execute_movement(self, route, distances, success_msg, route_key, dist_key):
        robot = self.robot
        self._reset_task()

        diag = robot.self_diagnose()
        if diag:
            robot.task_done = True
            robot.task_message = diag
            return

        if robot.encryption_decryption_module() and robot.hacked:
            robot.task_done = True
            robot.task_message = 'Обнаружена подмена задания'
            return

        if robot.battery_check():
            robot.task_done = True
            robot.task_message = 'Низкий заряд батареи'
            return

        route, distances = robot.lidar_check(route, distances)
        route, distances = robot.qr_check(route, distances)

        if CROSSING in route:
            robot.crossing_noticed = True

        actual_route = []
        actual_distances = []

        for coord, dist in zip(route, distances):
            if self._check_crossing(coord):
                robot.movement_interrupted = True
                break

            if robot.something_broken:
                robot.something_broken_noticed = True
                robot.movement_interrupted = True
                break

            robot.coordinates_qr = coord
            robot.update_obstacle_distance(dist)
            actual_route.append(coord)
            actual_distances.append(dist)

        self._update_wms_route(route_key, dist_key, actual_route, actual_distances)

        if robot.movement_interrupted:
            if robot.hacked and robot.hacked_noticed:
                robot.task_done = True
                robot.task_message = 'Движение прервано: подмена задания'
                return
            if robot.something_broken and robot.something_broken_noticed:
                robot.task_done = True
                robot.task_message = 'Движение прервано: неисправность'
                return
            if robot.crossing_noticed:
                robot.task_done = True
                robot.task_message = 'Движение прервано: перекрёсток занят'
                return
            robot.task_done = True
            robot.task_message = 'Движение прервано'
            return

        robot.task_done = True
        robot.task_message = success_msg

    def move_to_shelf(self, route, distances):
        robot = self.robot
        robot.is_move_shelf = True
        self._execute_movement(
            route, distances,
            'Робот добрался до стеллажа',
            'route_to_shelf', 'distances_to_shelf',
        )
        robot.is_move_shelf = False

    def move_to_station(self, route, distances):
        robot = self.robot
        robot.is_move_station = True
        self._execute_movement(
            route, distances,
            'Робот добрался до станции',
            'route_to_station', 'distances_to_station',
        )
        robot.is_move_station = False

    def grab_shelf(self):
        self._reset_task()
        msg = self.robot.grab_shelf()
        self.robot.task_done = True
        self.robot.task_message = msg

    def drop_shelf(self):
        self._reset_task()
        msg = self.robot.drop_shelf()
        self.robot.task_done = True
        self.robot.task_message = msg
