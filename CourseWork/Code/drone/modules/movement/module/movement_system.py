class MovementSystem:
    """Система передвижения робота."""

    def __init__(self, state):
        self.state = state

    def start_move_shelf(self):
        self.state.is_move_shelf = True

    def stop_move_shelf(self):
        self.state.is_move_shelf = False

    def start_move_station(self):
        self.state.is_move_station = True

    def stop_move_station(self):
        self.state.is_move_station = False

    def start_move_return_shelf(self):
        self.state.is_move_back = True

    def stop_move_return_shelf(self):
        self.state.is_move_back = False

    def start_move_home(self):
        self.state.is_move_home = True

    def stop_move_home(self):
        self.state.is_move_home = False

    def update_coordinates(self, coordinates_qr):
        self.state.coordinates_qr = coordinates_qr

    def update_route(self, route):
        self.state.route = route

    def set_speed(self, speed):
        self.state.speed = speed
