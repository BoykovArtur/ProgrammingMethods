from dataclasses import fields

from robot_status import RobotStatus

from import_ms import load_class

ChargeStateControl = load_class('charging', 'charge_state_control', 'ChargeStateControl')
ChargingController = load_class('charging', 'charging_controller', 'ChargingController')
CargoGripControl = load_class('cargo-grip', 'cargo_grip_control', 'CargoGripControl')
Manipulators = load_class('cargo-grip', 'manipulators', 'Manipulators')
EncryptionDecryption = load_class('communication', 'encryption_decryption', 'EncryptionDecryption')
LidarControl = load_class('coordination-lidar', 'lidar_control', 'LidarControl')
Lidars = load_class('coordination-lidar', 'lidars', 'Lidars')
QrRecognition = load_class('coordination-qr', 'qr_recognition', 'QrRecognition')
QrValidation = load_class('coordination-qr', 'qr_validation', 'QrValidation')
MovementSystem = load_class('movement', 'movement_system', 'MovementSystem')
SelfDiagnosticModule = load_class('self-diagnostic', 'self_diagnostic_module', 'SelfDiagnosticModule')


class Robot:
    """Фасад робота: объединяет подсистемы из drone/modules/."""

    def __init__(self, robot_id: str = None, avoid: int = 10, id: str = None):
        rid = robot_id or id
        if not rid:
            raise ValueError('robot_id required')
        self.state = RobotStatus(id=rid)
        self.obstacle_distance_avoidance = avoid

        self.lidars = Lidars()
        self.lidar_control = LidarControl(self.state, self.obstacle_distance_avoidance)
        self.qr_recognition = QrRecognition()
        self.qr_validation = QrValidation(self.state)
        self.encryption = EncryptionDecryption(self.state)
        self.movement = MovementSystem(self.state)
        self.charge_state = ChargeStateControl(self.state)
        self.charging = ChargingController(self.state)
        self.cargo_grip = CargoGripControl(self.state)
        self.manipulators = Manipulators(self.state, self.cargo_grip)
        self.self_diagnostic = SelfDiagnosticModule(
            self.state, self.obstacle_distance_avoidance
        )

    @property
    def id(self):
        return self.state.id

    @property
    def coordinates_qr(self):
        return self.state.coordinates_qr

    @coordinates_qr.setter
    def coordinates_qr(self, value):
        self.state.coordinates_qr = value

    @property
    def battery_percent(self):
        return self.state.battery_percent

    @battery_percent.setter
    def battery_percent(self, value):
        self.state.battery_percent = value

    @property
    def is_charging(self):
        return self.state.is_charging

    @is_charging.setter
    def is_charging(self, value):
        self.state.is_charging = value

    @property
    def is_move_shelf(self):
        return self.state.is_move_shelf

    @is_move_shelf.setter
    def is_move_shelf(self, value):
        self.state.is_move_shelf = value

    @property
    def is_move_station(self):
        return self.state.is_move_station

    @is_move_station.setter
    def is_move_station(self, value):
        self.state.is_move_station = value

    @property
    def take_shelf(self):
        return self.state.take_shelf

    @take_shelf.setter
    def take_shelf(self, value):
        self.state.take_shelf = value

    @property
    def is_move_back(self):
        return self.state.is_move_back

    @is_move_back.setter
    def is_move_back(self, value):
        self.state.is_move_back = value

    @property
    def is_move_home(self):
        return self.state.is_move_home

    @is_move_home.setter
    def is_move_home(self, value):
        self.state.is_move_home = value

    @property
    def route(self):
        return self.state.route

    @route.setter
    def route(self, value):
        self.state.route = value

    @property
    def speed(self):
        return self.state.speed

    @speed.setter
    def speed(self, value):
        self.state.speed = value

    @property
    def obstacle_distance(self):
        return self.state.obstacle_distance

    @obstacle_distance.setter
    def obstacle_distance(self, value):
        self.state.obstacle_distance = value

    @property
    def movement_interrupted(self):
        return self.state.movement_interrupted

    @movement_interrupted.setter
    def movement_interrupted(self, value):
        self.state.movement_interrupted = value

    @property
    def task_done(self):
        return self.state.task_done

    @task_done.setter
    def task_done(self, value):
        self.state.task_done = value

    @property
    def task_message(self):
        return self.state.task_message

    @task_message.setter
    def task_message(self, value):
        self.state.task_message = value

    @property
    def hacked(self):
        return self.state.hacked

    @hacked.setter
    def hacked(self, value):
        self.state.hacked = value

    @property
    def hacked_noticed(self):
        return self.state.hacked_noticed

    @hacked_noticed.setter
    def hacked_noticed(self, value):
        self.state.hacked_noticed = value

    @property
    def crossing_noticed(self):
        return self.state.crossing_noticed

    @crossing_noticed.setter
    def crossing_noticed(self, value):
        self.state.crossing_noticed = value

    @property
    def something_broken(self):
        return self.state.something_broken

    @something_broken.setter
    def something_broken(self, value):
        self.state.something_broken = value

    @property
    def something_broken_noticed(self):
        return self.state.something_broken_noticed

    @something_broken_noticed.setter
    def something_broken_noticed(self, value):
        self.state.something_broken_noticed = value

    @property
    def grab_correctly(self):
        return self.state.grab_correctly

    @grab_correctly.setter
    def grab_correctly(self, value):
        self.state.grab_correctly = value

    def get_status(self):
        return {
            'id': self.state.id,
            'coordinates_qr': self.state.coordinates_qr,
            'battery_percent': self.state.battery_percent,
            'is_charging': self.state.is_charging,
            'is_move_shelf': self.state.is_move_shelf,
            'is_move_station': self.state.is_move_station,
            'take_shelf': self.state.take_shelf,
            'is_move_back': self.state.is_move_back,
            'is_move_home': self.state.is_move_home,
            'route': self.state.route,
            'speed': self.state.speed,
            'obstacle_distance': self.state.obstacle_distance,
            'movement_interrupted': self.state.movement_interrupted,
            'task_done': self.state.task_done,
            'task_message': self.state.task_message,
            'hacked': self.state.hacked,
            'crossing_noticed': self.state.crossing_noticed,
            'something_broken': self.state.something_broken,
            'something_broken_noticed': self.state.something_broken_noticed,
            'grab_correctly': self.state.grab_correctly,
        }

    def start_move_shelf(self):
        return self.movement.start_move_shelf()

    def start_move_station(self):
        return self.movement.start_move_station()

    def start_move_return_shelf(self):
        return self.movement.start_move_return_shelf()

    def start_move_home(self):
        return self.movement.start_move_home()

    def stop_move_shelf(self):
        return self.movement.stop_move_shelf()

    def stop_move_station(self):
        return self.movement.stop_move_station()

    def stop_move_return_shelf(self):
        return self.movement.stop_move_return_shelf()

    def stop_move_home(self):
        return self.movement.stop_move_home()

    def start_charge(self):
        return self.charging.start_charge()

    def stop_charge(self):
        return self.charging.stop_charge()

    def grab_shelf(self):
        return self.manipulators.grab()

    def drop_shelf(self):
        return self.manipulators.drop()

    def update_coordinates_qr(self, coordinates_qr):
        return self.movement.update_coordinates(coordinates_qr)

    def update_battery_percent(self, battery_percent):
        return self.charge_state.update_level(battery_percent)

    def update_route(self, route):
        return self.movement.update_route(route)

    def update_obstacle_distance(self, distance):
        return self.lidar_control.update_distance(distance)

    def set_speed(self, speed):
        return self.movement.set_speed(speed)

    def lidar_check(self, route, distances):
        return self.lidar_control.filter_route(route, distances)

    def qr_check(self, route, distances):
        return self.qr_validation.validate_route(route, distances)

    def encryption_decryption_module(self):
        return self.encryption.check_compromised()

    def battery_check(self):
        return self.charge_state.is_low()

    def self_diagnose(self):
        return self.self_diagnostic.run()

    def reset(self):
        rid = self.state.id
        defaults = RobotStatus(id=rid)
        for field in fields(RobotStatus):
            if field.name == 'id':
                continue
            setattr(self.state, field.name, getattr(defaults, field.name))
