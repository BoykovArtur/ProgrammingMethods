import os
import sys
import requests
import time
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'wms'))
from wms import wms  # noqa: E402


ROBOT_URL = "http://localhost:8000"
ROBOT_1 = "wr-01"
ROBOT_2 = "wr-02"

class TestOperation(unittest.TestCase):
    def _wait_for_task(self, robot_id, timeout=30):
        """Ожидает завершения задачи и возвращает сообщение."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            resp = requests.get(f"{ROBOT_URL}/robot/task_result/{robot_id}")
            # Если эндпоинт вернёт 404 - задача не найдена (возможно, ещё не запущена)
            if resp.status_code == 404:
                time.sleep(0.5)
                continue
            data = resp.json()
            if data.get("status") == "done":
                return data.get("message")
            time.sleep(0.5)
        self.fail(f"Задача для робота {robot_id} не завершилась за {timeout} секунд")

    def test_delivery_task(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 23, 11, 13]})

        # запуск задачи
        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)

        final_message = self._wait_for_task(ROBOT_1)
        self.assertEqual(final_message, "Робот добрался до стеллажа")

    def test_ns1(self):
        # 1. Move to shelf
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 11, 11, 11]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        self.assertEqual(msg, "Робот добрался до стеллажа")

        # 2. Grab shelf
        start_resp = requests.post(f"{ROBOT_URL}/robot/start_grab_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        self.assertEqual(msg, "Робот закрепил стеллаж")

        # 3. Move to station
        requests.post(f"{ROBOT_URL}/test/set_route_to_station/{ROBOT_1}", json={"route_to_station": ["B1","B2","B3","B4"]})
        requests.post(f"{ROBOT_URL}/test/set_station_distances/{ROBOT_1}", json={"distances_to_station": [11, 11, 0, 11]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_station/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        distances_data = requests.post(f"{ROBOT_URL}/test/check_robot_obstacles/{ROBOT_1}").json()

        if any(distance < 10 for distance in distances_data["distances_to_station"]):
            self.fail(f"Робот врезался (расстояние до препятствия < 10)")
        return

    def test_ns2(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 23, 11, 13]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        self.assertEqual(msg, "Робот добрался до стеллажа")

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_grab_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        self.assertEqual(msg, "Робот закрепил стеллаж")

        # Невалидная координата "Wrong1" в маршруте
        requests.post(f"{ROBOT_URL}/test/set_route_to_station/{ROBOT_1}", json={"route_to_station": ["B1","B2","B3","Wrong"]})
        requests.post(f"{ROBOT_URL}/test/set_station_distances/{ROBOT_1}", json={"distances_to_station": [30, 33, 23, 15]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_station/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        route_data = requests.post(f"{ROBOT_URL}/test/check_robot_routes/{ROBOT_1}").json()

        if any(route == "Wrong" for route in route_data["route_to_station"]):
            self.fail(f"Робот врезался (робот выехал в запретную зону)")
        return

    def test_ns3(self):
        # Робот 1
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","Crossing","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_route_to_station/{ROBOT_1}", json={"route_to_station": ["temp","temp","temp","temp"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 23, 5, 13]})
        requests.post(f"{ROBOT_URL}/test/set_station_distances/{ROBOT_1}", json={"distances_to_station": [11, 12, 13, 14]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        route_data = requests.post(f"{ROBOT_URL}/test/check_robot_routes/{ROBOT_1}").json()
        crossing_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
        if any(route == "Crossing" for route in route_data["route_to_shelf"]) and not crossing_data["crossing_noticed"]:
            self.fail(f"Робот врезался (роботы врезались)")

        # Робот 2
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_2}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_2}", json={"route_to_shelf": ["B1","B2","Crossing","B4"]})
        requests.post(f"{ROBOT_URL}/test/set_route_to_station/{ROBOT_2}", json={"route_to_station": ["temp","temp","temp","temp"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_2}", json={"distances_to_shelf": [15, 14, 5, 16]})
        requests.post(f"{ROBOT_URL}/test/set_station_distances/{ROBOT_2}", json={"distances_to_station": [11, 12, 13, 14]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_2}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_2)

        route_data = requests.post(f"{ROBOT_URL}/test/check_robot_routes/{ROBOT_2}").json()
        crossing_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_2}").json()
        if any(route == "Crossing" for route in route_data["route_to_shelf"]) and not crossing_data["crossing_noticed"]:
            self.fail(f"Робот врезался (роботы врезались)")
        return

    def test_ns4(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/break_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 11, 11, 0]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        robot_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
        if robot_data["something_broken"]and not robot_data["something_broken_noticed"]:
            self.fail(f"Робот не заметил поломку и врезался")
        return

    def test_ns5(self):
        # Робот сброшен, захвата не было
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/grab_weak/{ROBOT_1}")
        start_resp = requests.post(f"{ROBOT_URL}/robot/start_grab_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        robot_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
        if not robot_data["grab_correctly"]:
            self.fail(f"Робот уронил стеллаж")
        self.assertEqual(msg, "Робот закрепил стеллаж")

    def test_ns7(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        #Подмена задания
        requests.post(f"{ROBOT_URL}/test/hack_robot/{ROBOT_1}")

        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 23, 5, 13]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        robot_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
        if robot_data["hacked"]and not robot_data["hacked_noticed"]:
            self.fail(f"Робот выполняет неправильное задание")
        return

    def test_ns10(self):
        # Робот1 стоит на A3, робот2 едет к стеллажу, маршрут которого включает A3
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_2}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_2}", json={"route_to_shelf": ["B1","B2","Crossing","B4"]})
        requests.post(f"{ROBOT_URL}/test/set_route_to_station/{ROBOT_2}", json={"route_to_station": ["B1","B2","B3","B4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_2}", json={"distances_to_shelf": [15, 14, 5, 16]})

        # Устанавливаем координаты робота1 в A3 (препятствие для робота2)
        requests.post(f"{ROBOT_URL}/test/set_coordinates/{ROBOT_1}/Crossing")

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_2}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_2)

        route_data = requests.post(f"{ROBOT_URL}/test/check_robot_routes/{ROBOT_2}").json()
        crossing_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_2}").json()
        if any(route == "Crossing" for route in route_data["route_to_shelf"]) and not crossing_data["crossing_noticed"]:
            self.fail(f"Затор")
        return

    def test_ns11(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["B1","B2","B3","B4"]})
        requests.post(f"{ROBOT_URL}/test/set_route_to_station/{ROBOT_1}", json={"route_to_station": ["A1","A2","NotAllowed","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_station_distances/{ROBOT_1}", json={"distances_to_station": [11, 23, 0, 13]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_station/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        route_data = requests.post(f"{ROBOT_URL}/test/check_robot_routes/{ROBOT_1}").json()

        if any(route == "NotAllowed" for route in route_data["route_to_station"]):
            self.fail(f"Робот выехал в запрещенную зону")
        self.assertEqual(msg, "Робот добрался до станции")

    def test_ns12(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        #Подмена задания
        requests.post(f"{ROBOT_URL}/test/hack_robot/{ROBOT_1}")

        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 23, 5, 13]})

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        robot_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
        if robot_data["hacked"]and not robot_data["hacked_noticed"]:
            self.fail(f"Робот выполняет неправильное задание")
        self.assertNotEqual(msg, "Робот добрался до стеллажа")

    def test_ns13(self):
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        requests.post(f"{ROBOT_URL}/test/set_route_to_shelf/{ROBOT_1}", json={"route_to_shelf": ["A1","A2","A3","A4"]})
        requests.post(f"{ROBOT_URL}/test/set_shelf_distances/{ROBOT_1}", json={"distances_to_shelf": [11, 23, 11, 13]})

        battery_level = 9

        requests.post(f"{ROBOT_URL}/test/set_battery/{ROBOT_1}/{battery_level}")

        # запуск задачи
        start_resp = requests.post(f"{ROBOT_URL}/robot/start_move_to_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)

        final_message = self._wait_for_task(ROBOT_1)
        self.assertNotEqual(final_message, "Робот добрался до стеллажа")

    def test_ns15(self):
        # Робот сброшен, захвата не было
        requests.post(f"{ROBOT_URL}/test/reset_robot/{ROBOT_1}")
        start_resp = requests.post(f"{ROBOT_URL}/robot/start_grab_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)
        requests.post(f"{ROBOT_URL}/test/grab_weak/{ROBOT_1}")

        start_resp = requests.post(f"{ROBOT_URL}/robot/start_drop_shelf/{ROBOT_1}")
        self.assertEqual(start_resp.status_code, 202)
        msg = self._wait_for_task(ROBOT_1)

        robot_data = requests.get(f"{ROBOT_URL}/robot/status/{ROBOT_1}").json()
        if not robot_data["grab_correctly"]:
            self.fail(f"Робот уронил стеллаж")
        self.assertEqual(msg, "Робот закрепил стеллаж")

if __name__ == "__main__":
    unittest.main()