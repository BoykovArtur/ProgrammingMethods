import sys
from pathlib import Path
_idl = Path(__file__).resolve().parents[3] / 'shared' / 'idl'
if str(_idl) not in sys.path:
    sys.path.insert(0, str(_idl))
from robot_status import RobotStatus


class LidarControl:
    """Модуль контроля состояния лидаров [MS]."""

    def __init__(self, state: RobotStatus, avoidance_threshold: int):
        self._state = state
        self._threshold = avoidance_threshold

    def update_distance(self, distance: int):
        self._state.obstacle_distance = distance
        return f'Расстояние до препятствия {distance}'

    def filter_route(self, route, distances):
        filtered_route = []
        filtered_distances = []
        for r, d in zip(route, distances):
            if d >= self._threshold:
                filtered_route.append(r)
                filtered_distances.append(d)

        new_route = []
        new_distances = []
        i = 0
        while i < len(filtered_distances):
            if i + 2 >= len(filtered_distances):
                new_route.append(filtered_route[i])
                new_distances.append(filtered_distances[i])
                i += 1
                continue
            if (
                filtered_distances[i]
                == filtered_distances[i + 1]
                == filtered_distances[i + 2]
            ):
                self._state.something_broken_noticed = True
                i += 3
                continue
            new_route.append(filtered_route[i])
            new_distances.append(filtered_distances[i])
            i += 1
        return new_route, new_distances
