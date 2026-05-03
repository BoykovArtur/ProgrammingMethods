from flask import Flask, jsonify, request
from pathlib import Path
import json
import time
import requests
import os
import threading
from werkzeug.exceptions import HTTPException
from wms import wms_stub

MANAGMENT_URL = "http://management_system:8000"

HOST = "0.0.0.0"
PORT = 8000
MODULE_NAME = os.getenv("MODULE_NAME")
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

class Robot:
    def __init__(self, id, avoid=10):
        self.id = id
        self.coordinates_qr = ''
        self.battery_percent = 100
        self.is_charging = False
        self.is_move_shelf = False
        self.is_move_station = False
        self.take_shelf = False
        self.is_move_back = False
        self.is_move_home = False
        self.route = []  # пример списка: ['A1', 'A2', 'A3']
        self.speed = 0
        self.obstacle_distance_avoidance = avoid
        self.obstacle_distance = 10

    def start_move_shelf(self):
        if not self.is_move_shelf:
            self.is_move_shelf = True
            return "Робот начал движение к стеллажу."
        return "Робот уже движется к стеллажу."

    def start_move_station(self):
        if not self.is_move_station:
            self.is_move_station = True
            return f"Робот начал движение к станции."
        else:
            return f"Робот уже движется к станции."
    
    def start_take_shelf(self):
        if not self.take_shelf:
            self.take_shelf = True
            return f"Робот начал захват стеллажа."
        else:
            return f"Робот уже захватывает стеллаж."
    
    def start_move_return_shelf(self):
        if not self.is_move_back:
            self.is_move_back = True
            return f"Робот начал возврат стеллажа."
        else:
            return f"Робот уже движется возвращать стеллаж."
    def start_move_home(self):
        if not self.is_move_home:
            self.is_move_home = True
            return f"Робот начал движение в свою зону отдыха."
        else:
            return f"Робот уже движется в свою точку отдыха."
    
    def start_charge(self):
        if not self.is_charging:
            self.is_charging = True
            return "Робот начал заряжаться."
        return "Робот уже заряжается."

    def stop_move_shelf(self):
        if self.is_move_shelf:
            self.is_move_shelf = False
            return f"Робот остановил движение к стеллажу."
        else:
            return f"Робот не движется к стеллажу."
    
    def stop_move_station(self):
        if self.is_move_station:
            self.is_move_station = False
            return f"Робот остановил движение к станции."
        else:
            return f"Робот не движется к станции."
    
    def stop_take_shelf(self):
        if self.take_shelf:
            self.take_shelf = False
            return f"Робот прекратил захват стеллажа."
        else:
            return f"Робот не захватывает стеллаж."
    
    def stop_move_return_shelf(self):
        if self.is_move_back:
            self.is_move_back = False
            return f"Робот доехал до точки возврата стеллажа."
        else:
            return f"Робот не ехал к точке возврата стеллажа."

    def stop_move_home(self):
        if self.is_move_home:
            self.is_move_home = False
            return f"Робот доехал до точки отдыха."
        else:
            return f"Робот не ехал к точке отдыха."
    
    def stop_charge(self):
        if self.is_charging:
            self.is_charging = False
            return f"Робот прекратил зарядку."
        else:
            return f"Робот не заряжается."
    
    def self_diagnose(self):
        if self.battery_percent <= 10:
            return "Низкая зарядка батареи"
        if self.is_move_shelf and self.obstacle_distance < self.obstacle_distance_avoidance:
            self.is_move_shelf = False
            return f"Расстояние до препятствия меньше безопасного значения. Невозможно добраться до стеллажа"
        if self.is_move_station and self.obstacle_distance<self.obstacle_distance_avoidance:
            self.is_move_station = False
            return f"Расстояние до препятствия меньше безопасного значения. Невозможно добраться до станции"
        if self.is_move_back and self.obstacle_distance<self.obstacle_distance_avoidance:
            self.is_move_back = False
            return f"Расстояние до препятствия меньше безопасного значения. Невозможно вернуть стеллаж"
        if self.is_move_home and self.obstacle_distance<self.obstacle_distance_avoidance:
            self.is_move_home = False
            return f"Расстояние до препятствия меньше безопасного значения. Невозможно вернуться на базу"

    def get_status(self):
        return {
            "id": self.id,
            "coordinates_qr": self.coordinates_qr,
            "battery_percent": self.battery_percent,
            "is_charging": self.is_charging,
            "is_move_shelf": self.is_move_shelf,
            "is_move_station": self.is_move_station,
            "take_shelf": self.take_shelf,
            "is_move_back": self.is_move_back,
            "is_move_home": self.is_move_home,
            "route": self.route,
            "speed": self.speed,
            "obstacle_distance": self.obstacle_distance,
        }
    def update_coordinates_qr(self, coordinates_qr):
        self.coordinates_qr = coordinates_qr
        return f"Координаты QR робота изменены на {coordinates_qr}."
    def update_battery_percent(self, battery_percent):
        self.battery_percent = battery_percent
        return f"Уровень заряда робота изменен на {battery_percent} %."

    def update_route(self, route):
        self.route = route
        return f"Маршрут робота изменен на {route}."
    def update_obstacle_distance(self,distance):
        self.obstacle_distance = distance
        return f"Расстояние до препятствия {distance}"

    def set_speed(self, speed):
        if self.is_move_shelf or self.is_move_station or self.is_move_back:
            self.speed = speed
            return f"Скорость робота изменена на {speed} м/с."
        else:
            return f"Робот не движется."
def simulate_move_shelf_and_station(robot, route_to_shelf, route_to_station, distances_to_shelf,distances_to_station):
    robot.stop_charge()
    robot.start_move_shelf()
    while robot.is_move_shelf:
        for i in range(len(route_to_shelf)):
            robot.update_coordinates_qr(route_to_shelf[i])
            robot.update_battery_percent(robot.battery_percent - 1)
            robot.update_obstacle_distance(distances_to_shelf[i])
            diagnosis = robot.self_diagnose()
            requests.post(
                f"{MANAGMENT_URL}/telemetry/{robot.id}",
                 json={"status": robot.get_status(), "diagnosis": diagnosis},
                timeout=5)
            time.sleep(1)

    if robot.coordinates_qr != route_to_shelf[len(route_to_shelf)]:
        return f"Неудалось добраться до стеллажа"
    robot.stop_move_shelf()
    robot.start_take_shelf()

    requests.post(
        f"{MANAGMENT_URL}/telemetry/{robot.id}",
        json={"status": robot.get_status()},
        timeout=5)

    robot.start_move_station()
    while robot.is_move_station:
        for i in range(len(route_to_station)):
            robot.update_coordinates_qr(route_to_station[i])
            robot.update_battery_percent(robot.battery_percent - 1)
            robot.update_obstacle_distance(distances_to_station[i])
            diagnosis = robot.self_diagnose()
            requests.post(
                f"{MANAGMENT_URL}/telemetry/{robot.id}",
                json={"status": robot.get_status(), "diagnosis": diagnosis},
                timeout=5)
            time.sleep(1)

    if robot.coordinates_qr != route_to_station[len(route_to_station)]:
        return f"Неудалось добраться до станции"
    robot.stop_move_station()
    robot.stop_take_shelf()
    return f"Задание успешно выполнено"
def simulate_move_return_and_home(robot, route_to_return, route_to_home,distances_to_return,distances_to_home):
    robot.start_take_shelf()
    robot.start_move_return_shelf()
    while robot.is_move_back:
        for i in range(len(route_to_return)):
            robot.update_coordinates_qr(route_to_return[i])
            robot.update_battery_percent(robot.battery_percent - 1)
            robot.update_obstacle_distance(distances_to_return[i])
            diagnosis = robot.self_diagnose()

            try:
                requests.post(
                    f"{MANAGMENT_URL}/telemetry/{robot.id}",
                    json={"status": robot.get_status(), "diagnosis": diagnosis},
                    timeout=5,
                )
            except requests.RequestException:
                pass
            time.sleep(1)
    if robot.coordinates_qr != route_to_return[len(route_to_return)]:
        return f"Неудалось вернуть стеллаж"
    robot.stop_move_return_shelf()
    robot.stop_take_shelf()
    robot.start_move_home()
    while robot.is_move_home:
        for i in range(len(route_to_home)):
            robot.update_coordinates_qr(route_to_home[i])
            robot.update_battery_percent(robot.battery_percent - 1)
            robot.update_obstacle_distance(distances_to_home[i])
            diagnosis = robot.self_diagnose()
            requests.post(f"{MANAGMENT_URL}/telemetry/{robot.id}", json={"status": robot.get_status(), "diagnosis": diagnosis}, timeout=5)
            time.sleep(1)
    if robot.coordinates_qr != route_to_return[len(route_to_home)]:
        return f"Неудалось вернуться на базу"
    robot.stop_move_home()
    robot.start_charge()
    return f"Задание успешно выполнено"


def _send_telemetry(robot, diagnosis=None):
    payload = {"status": robot.get_status()}
    if diagnosis is not None:
        payload["diagnosis"] = diagnosis
    requests.post(
        f"{MANAGMENT_URL}/telemetry/{robot.id}",
        json=payload,
        timeout=5)


def load_robots_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        robots_data = json.load(file)
        return [Robot(**robot) for robot in robots_data]



BASE_DIR = Path(__file__).resolve().parent
robots = load_robots_from_json(f'{BASE_DIR}/data/robots.json')


def _robot_by_id(robot_id):
    for r in robots:
        if str(r.id).lower() == str(robot_id).lower():
            return r
    return None


@app.route("/robot/status/all", methods=["GET"])
def get_all_robot_statuses():
    statuses = [r.get_status() for r in robots]
    return jsonify(statuses)


@app.route("/robot/status/<string:robot_id>", methods=["GET"])
def get_robot_status(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    return jsonify(robot.get_status())

@app.route("/robot/move_shelf/start/<string:robot_id>", methods=["POST"])
def start_move_shelf_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.start_move_shelf()
    return jsonify({"message": message})


@app.route("/robot/move_shelf/stop/<string:robot_id>", methods=["POST"])
def stop_move_shelf_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.stop_move_shelf()
    return jsonify({"message": message})


@app.route("/robot/move_station/start/<string:robot_id>", methods=["POST"])
def start_move_station_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.start_move_station()
    return jsonify({"message": message})


@app.route("/robot/move_station/stop/<string:robot_id>", methods=["POST"])
def stop_move_station_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.stop_move_station()
    return jsonify({"message": message})

@app.route("/robot/take_shelf/start/<string:robot_id>", methods=["POST"])
def start_take_shelf_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.start_take_shelf()
    return jsonify({"message": message})


@app.route("/robot/take_shelf/stop/<string:robot_id>", methods=["POST"])
def stop_take_shelf_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.stop_take_shelf()
    return jsonify({"message": message})


@app.route("/robot/return_shelf/start/<string:robot_id>", methods=["POST"])
def start_return_shelf_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.start_move_return_shelf()
    return jsonify({"message": message})


@app.route("/robot/return_shelf/stop/<string:robot_id>", methods=["POST"])
def stop_return_shelf_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.stop_move_return_shelf()
    return jsonify({"message": message})


@app.route("/robot/move_home/start/<string:robot_id>", methods=["POST"])
def start_move_home_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.start_move_home()
    return jsonify({"message": message})


@app.route("/robot/move_home/stop/<string:robot_id>", methods=["POST"])
def stop_move_home_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.stop_move_home()
    return jsonify({"message": message})


@app.route("/robot/charge/start/<string:robot_id>", methods=["POST"])
def start_charge_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.start_charge()
    return jsonify({"message": message})


@app.route("/robot/charge/stop/<string:robot_id>", methods=["POST"])
def stop_charge_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    message = robot.stop_charge()
    return jsonify({"message": message})


@app.route("/robot/diagnose/<string:robot_id>", methods=["POST"])
def diagnose_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    msg = robot.self_diagnose()
    if msg:
        return jsonify({"message": msg})
    return jsonify({"message": "ОК"})

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code

@app.route("/robot/start_move_shelf_and_station/<string:robot_id>", methods=["POST"])
def start_delivery_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    
    if robot.is_move_shelf or robot.is_move_station:
        return jsonify({"error": "Робот уже выполняет задачу доставки."}), 409

    route_data = wms_stub.routes.get(robot.id)
    if not route_data:
        return jsonify({"error": "Для робота нет маршрута в WMS."}), 404

    message = robot.start_move_shelf()
    route_to_shelf = route_data["route_to_shelf"]
    route_to_station = route_data["route_to_station"]
    distances_to_shelf = route_data["distances_to_shelf"]
    distances_to_station = route_data["distances_to_station"]
    thread = threading.Thread(
        target=simulate_move_shelf_and_station,
        args=(robot, route_to_shelf, route_to_station, distances_to_shelf, distances_to_station),
        daemon=False
    )
    thread.start()
    
    return jsonify({"message": message})


@app.route("/robot/start_move_return_and_home/<string:robot_id>", methods=["POST"])
def start_return_home_route(robot_id):
    robot = _robot_by_id(robot_id)
    if not robot:
        return jsonify({"error": "Робот не найден."}), 404
    
    if robot.is_move_back or robot.is_move_home:
        return jsonify({"error": "Робот уже выполняет задачу возврата."}), 409
    return_data = wms_stub.return_routes.get(robot.id)
    if not return_data:
        return jsonify({"error": "Для робота нет маршрута возврата в WMS."}), 404

    robot.start_take_shelf()
    message = robot.start_move_return_shelf()
    route_to_return = return_data["route_to_return"]
    route_to_home = return_data["route_to_home"]
    distances_to_return = return_data["distances_to_return"]
    distances_to_home = return_data["distances_to_home"]

    thread = threading.Thread(
        target=simulate_move_return_and_home,
        args=(robot, route_to_return, route_to_home, distances_to_return, distances_to_home),
        daemon=False
    )
    thread.start()
    
    return jsonify({"message": message})

def start_web():
    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()

def main():
    start_web()