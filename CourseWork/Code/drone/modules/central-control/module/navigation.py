class Navigation:
    """Система навигации [CL] — объединяет данные QR и лидара."""

    def __init__(self, robot):
        self._robot = robot

    def prepare_route_to_shelf(self, route_data: dict):
        route, distances = self._robot.qr_check(
            route_data['route_to_shelf'],
            route_data['distances_to_shelf'],
        )
        route, distances = self._robot.lidar_check(route, distances)
        route_data['route_to_shelf'] = route
        route_data['distances_to_shelf'] = distances
        return route, distances

    def prepare_route_to_station(self, route_data: dict):
        route, distances = self._robot.qr_check(
            route_data['route_to_station'],
            route_data['distances_to_station'],
        )
        route, distances = self._robot.lidar_check(route, distances)
        route_data['route_to_station'] = route
        route_data['distances_to_station'] = distances
        return route, distances
