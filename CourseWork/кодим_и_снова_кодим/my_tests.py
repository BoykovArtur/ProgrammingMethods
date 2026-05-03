import requests
from wms import wms


ROBOT_URL = "http://localhost:8000"
ROBOT_1 = "wr-01"
ROBOT_2 = "wr-02"
SAFE_DISTANCE = 10


def test_ns1_lidar_did_not_detect_human():
    actual_distance_to_human = 5

    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status["obstacle_distance"] = 30
    lidar_reading = status["obstacle_distance"]

    if lidar_reading >= SAFE_DISTANCE and actual_distance_to_human < SAFE_DISTANCE:
        print("Робот ошибочно решил что путь свободен и наехал на человека!!!")
        assert False


def test_ns2_qr_code_read_error():
    #Пусть опреатор стоит на A0
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status["route"] = ['A1', 'B1', 'C1', 'E1', 'F1']
    status['coordinates_qr'] = ['A0']
    status['is_move_station'] = True
    status["obstacle_distance"] = 5

    wrong_qr_point = status["coordinates_qr"] not in status["route"] and status["is_move_station"]
    if wrong_qr_point and status["obstacle_distance"] < SAFE_DISTANCE:
        print("Ошибка QR: робот приехал в неверную точку и опасно сблизился с оператором!!!")
        assert False


def test_ns3_conflicting_wms_routes_two_robots():
    status_1 = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status_2 = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_2}").json()

    route_1 = wms.routes[ROBOT_1]["route_to_station"]
    route_2 = wms.routes[ROBOT_2]["route_to_station"]

    status_1["is_move_station"] = True
    status_2["is_move_station"] = True
    status_1["coordinates_qr"] = 'B2'
    status_2["coordinates_qr"] = 'B2'

    robots_move_to_station = status_1["is_move_station"] and status_2["is_move_station"]
    same_point_now = status_1["coordinates_qr"] == status_2["coordinates_qr"]
    conflict_by_wms = bool(set(route_1) & set(route_2))

    if robots_move_to_station and (same_point_now or conflict_by_wms):
        print("НС-3: WMS выдал конфликтующие маршруты двум роботам, возможна авария!!!")
        assert False


def test_ns4_lidar_failed_and_selfcheck_missed():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status["is_move_station"] = True
    status["obstacle_distance"] = 20

    actual_obstacle_distance = 3
    if (status["is_move_shelf"] or status["is_move_station"]) and status["obstacle_distance"] >= SAFE_DISTANCE and actual_obstacle_distance < SAFE_DISTANCE:
        print("Лидар отказал, самодиагностика не сработала, робот врезался в препятствие!!!")
        assert False


def test_ns5_false_gripper_fixation():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status["is_move_station"] = True

    robot_moves_with_shelf = status["is_move_station"] or status["is_move_back"]
    shelf_lost = not status["take_shelf"]

    if robot_moves_with_shelf and shelf_lost:
        print("Система захвата ошиблась: стеллаж не был зафиксирован и упал!!!")
        assert False

def test_ns_6():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    route_1 = wms.routes[ROBOT_1]["route_to_shelf"]
    route_1 = ["A1", "A2", "A3", "A4"] #произошла ошибка - замена пути на ложный
    if route_1[-1] != wms.routes[ROBOT_1]["route_to_shelf"]:
        print("Произошла ошибка указания пути от WMS, робот приехал не к тому стеллажу!!!")
        assert False

def test_ns9_traffic_jam_two_robots():
    status_1 = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status_2 = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_2}").json()
    status_1["route"] = ["A4", 'A3', 'A2', 'A1']
    status_2["route"] = ["A1", 'A2', 'A3', 'A4']
    route_1 = status_1["route"]
    route_2 = status_2["route"]

    both_have_routes = len(route_1) > 0 and len(route_2) > 0
    routes_intersect = bool(set(route_1) & set(route_2))

    if both_have_routes and routes_intersect:
        print("НС-9: пересекающиеся маршруты привели к затору двух роботов!!!")
        assert False


def test_ns10_wms_connection_lost_robot_blocks_path():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()

    status["route"] = []
    wms_connection_lost = len(status["route"]) == 0
    if wms_connection_lost:
        print("Потеря связи с WMS: робот остановился в проходе и блокирует движение!!!")
        assert False


def test_ns11_route_outside_authorized_zone():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()

    status['route'] = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1']
    forbidden_columns = {"E", "F", "G"}
    for point in status["route"]:
        if str(point)[0] in forbidden_columns:
            print("Робот выехал за пределы авторизованной зоны!!!")
            assert False


def test_ns12_unauthorized_wms_commands():
    fake_wms_comandes = { 
                "route_to_shelf": ["A1", "A2", "A3", "A4"],
                "route_to_station": ["B1", "B2"],
                "distances_to_shelf": [15, 12, 10, 7],
                "distances_to_station": [9, 5]
            }
    fake_wms_comandes_return = {
                "route_to_return": ["C1", "C2"],
                "route_to_home": ["D1"],
                "distances_to_return": [7, 5],
                "distances_to_home": [3]
            }

    true_wms_comandes = wms.routes[ROBOT_1]
    true_wms_comandes_return = wms.return_routes[ROBOT_1]

    if fake_wms_comandes != true_wms_comandes or fake_wms_comandes_return != true_wms_comandes_return:
        print("Атака на канал связи, команды не авторизованы!!!")
        assert False


def test_ns13_wrong_battery_estimation():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()

    true_battery_percent = 9
    if true_battery_percent != status["battery_percent"] and true_battery_percent <= 10:
        print("Модуль заряда ошибся: реальный заряд критически мал!!!")
        assert False


def test_ns15_gripper_failed_while_moving():
    status = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
    status["is_move_station"] = True
    status["take_shelf"] = False

    robot_is_moving = status["is_move_shelf"] or status["is_move_station"] or status["is_move_back"] or status["is_move_home"]
    if robot_is_moving and not status["take_shelf"]:
        print("Робот бросил стеллаж во время движения!!!")
        assert False
