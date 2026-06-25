# Система управления складом (СУС, WMS) — внешняя по отношению к дрону
import json
import os
from datetime import datetime

TELEMETRY_FILE = os.getenv('WMS_TELEMETRY_FILE', 'wms_telemetry.json')


class WMSSubsystem:
    def __init__(self):
        self.routes = {
            'wr-01': {
                'route_to_shelf': ['X1', 'X2', 'X3', 'X4'],
                'route_to_station': ['Y1', 'Y2'],
                'distances_to_shelf': [20, 18, 14, 11],
                'distances_to_station': [11, 6],
            },
            'wr-02': {
                'route_to_shelf': ['A1', 'A2', 'A3', 'A4'],
                'route_to_station': ['B1', 'B2'],
                'distances_to_shelf': [15, 12, 10, 7],
                'distances_to_station': [9, 5],
            },
        }
        self.return_routes = {
            'wr-01': {
                'route_to_return': ['Z1', 'Z2'],
                'route_to_home': ['H1'],
                'distances_to_return': [8, 6],
                'distances_to_home': [4],
            },
            'wr-02': {
                'route_to_return': ['C1', 'C2'],
                'route_to_home': ['D1'],
                'distances_to_return': [7, 5],
                'distances_to_home': [3],
            },
        }
        self.telemetry_log = []
        self.security_log = []
        self.robot_stats = {}

    def receive_telemetry(self, robot_id, status, diagnosis=None):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'robot_id': robot_id,
            'status': status,
            'diagnosis': diagnosis,
        }
        self.telemetry_log.append(entry)
        if robot_id not in self.robot_stats:
            self.robot_stats[robot_id] = {
                'last_seen': datetime.now().isoformat(),
                'max_battery': 100,
                'min_battery': 100,
                'last_coordinates': status.get('coordinates_qr'),
                'total_movements': 0,
            }
        stats = self.robot_stats[robot_id]
        stats['last_seen'] = datetime.now().isoformat()
        stats['last_coordinates'] = status.get('coordinates_qr')
        stats['min_battery'] = min(
            stats['min_battery'], status.get('battery_percent', 100)
        )
        if status.get('is_move_shelf') or status.get('is_move_station'):
            stats['total_movements'] += 1
        print(
            f'[WMS] Телеметрия {robot_id}: батарея={status.get("battery_percent")}%'
        )
        with open(TELEMETRY_FILE, 'a', encoding='utf-8') as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
        return {'status': 'ok', 'stored': True}

    def receive_security_alert(self, robot_id, alert_type, status):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'robot_id': robot_id,
            'alert_type': alert_type,
            'status': status,
        }
        self.security_log.append(entry)
        print(f'[WMS] SECURITY ALERT {robot_id}: {alert_type}')
        return {'status': 'ok', 'alert_recorded': True}

    def get_telemetry_history(self, robot_id=None):
        if robot_id:
            return [t for t in self.telemetry_log if t['robot_id'] == robot_id]
        return self.telemetry_log

    def get_robot_statistics(self, robot_id):
        return self.robot_stats.get(robot_id, {})

    def get_all_statistics(self):
        return self.robot_stats

    def get_security_log(self):
        return self.security_log


wms = WMSSubsystem()
