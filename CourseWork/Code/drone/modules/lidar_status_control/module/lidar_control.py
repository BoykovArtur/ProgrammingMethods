class LidarControl:
    """Фильтрация маршрута по показаниям лидара."""

    def __init__(self, state, threshold=10):
        self.state = state
        self._threshold = threshold

    def update_distance(self, distance):
        self.state.obstacle_distance = distance

    def filter_route(self, route, distances):
        filtered_route = []
        filtered_distances = []
        for coord, dist in zip(route, distances):
            if dist <= 0:
                break
            filtered_route.append(coord)
            filtered_distances.append(dist)
        return filtered_route, filtered_distances
