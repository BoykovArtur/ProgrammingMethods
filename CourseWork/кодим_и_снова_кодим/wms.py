# wms.py
import json
from datetime import datetime

class WMSSub:
    def __init__(self):
        # Маршруты доставки
        self.routes = {
            "wr-01": {
                "route_to_shelf": ["X1", "X2", "X3", "X4"],
                "route_to_station": ["Y1", "Y2"],
                "distances_to_shelf": [20, 18, 14, 9],
                "distances_to_station": [11, 6]
            },
            "wr-02": {
                "route_to_shelf": ["A1", "A2", "A3", "A4"],
                "route_to_station": ["B1", "B2"],
                "distances_to_shelf": [15, 12, 10, 7],
                "distances_to_station": [9, 5]
            }
        }
        
        # Маршруты возврата
        self.return_routes = {
            "wr-01": {
                "route_to_return": ["Z1", "Z2"],
                "route_to_home": ["H1"],
                "distances_to_return": [8, 6],
                "distances_to_home": [4]
            },
            "wr-02": {
                "route_to_return": ["C1", "C2"],
                "route_to_home": ["D1"],
                "distances_to_return": [7, 5],
                "distances_to_home": [3]
            }
        }
        
        # Хранилище для телеметрии
        self.telemetry_log = []
        
        # Статистика роботов
        self.robot_stats = {}
    
    def receive_telemetry(self, robot_id, status, diagnosis=None):
        """Принимает и сохраняет телеметрию от робота"""
        telemetry_entry = {
            "timestamp": datetime.now().isoformat(),
            "robot_id": robot_id,
            "status": status,
            "diagnosis": diagnosis
        }
        
        # Сохраняем в лог
        self.telemetry_log.append(telemetry_entry)
        
        # Обновляем статистику
        if robot_id not in self.robot_stats:
            self.robot_stats[robot_id] = {
                "last_seen": datetime.now().isoformat(),
                "max_battery": 100,
                "min_battery": 100,
                "last_coordinates": status.get("coordinates_qr"),
                "total_movements": 0
            }
        
        stats = self.robot_stats[robot_id]
        stats["last_seen"] = datetime.now().isoformat()
        stats["last_coordinates"] = status.get("coordinates_qr")
        stats["min_battery"] = min(stats["min_battery"], status.get("battery_percent", 100))
        
        # Считаем движения
        if status.get("is_move_shelf") or status.get("is_move_station"):
            stats["total_movements"] += 1
        
        print(f"[WMS] Получена телеметрия от {robot_id}: батарея={status.get('battery_percent')}%, "
            f"координаты={status.get('coordinates_qr')}")
        
        # Сохраняем в файл
        with open('wms_telemetry.json', 'a', encoding='utf-8') as f:
            json.dump(telemetry_entry, f, ensure_ascii=False)
            f.write('\n')
        
        return {"status": "ok", "stored": True}
    
    def get_telemetry_history(self, robot_id=None):
        """Получить историю телеметрии"""
        if robot_id:
            return [t for t in self.telemetry_log if t["robot_id"] == robot_id]
        return self.telemetry_log
    
    def get_robot_statistics(self, robot_id):
        """Получить статистику робота"""
        return self.robot_stats.get(robot_id, {})
    
    def get_all_statistics(self):
        """Получить статистику всех роботов"""
        return self.robot_stats

# Создаем глобальный экземпляр WMS
wms = WMSSub()