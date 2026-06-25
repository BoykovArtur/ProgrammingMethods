INVALID_QR = {'Wrong', 'NotAllowed', 'Wrong1'}


class QrValidation:
    """Валидация QR-координат маршрута."""

    def __init__(self, state):
        self.state = state

    def validate_route(self, route, distances):
        filtered_route = []
        filtered_distances = []
        for coord, dist in zip(route, distances):
            if coord in INVALID_QR:
                break
            filtered_route.append(coord)
            filtered_distances.append(dist)
        return filtered_route, filtered_distances
