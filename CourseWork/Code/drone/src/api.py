import threading

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

import sys
from pathlib import Path

_wms_root = Path(__file__).resolve().parents[2] / 'wms'
if str(_wms_root) not in sys.path:
    sys.path.insert(0, str(_wms_root))
from wms import wms  # noqa: E402

_drone_shared = Path(__file__).resolve().parents[1] / 'shared'
if str(_drone_shared) not in sys.path:
    sys.path.insert(0, str(_drone_shared))
from kafka_publisher import notify_task  # noqa: E402


def create_app(ccs, host='0.0.0.0', port=8000):
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    def _robot(robot_id):
        return ccs.robot_by_id(robot_id)

    @app.route('/robot/status/all', methods=['GET'])
    def get_all_robot_statuses():
        return jsonify([r.get_status() for r in ccs.robots])

    @app.route('/robot/status/<string:robot_id>', methods=['GET'])
    def get_robot_status(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден.'}), 404
        status = robot.get_status()
        status['hacked_noticed'] = robot.hacked_noticed
        return jsonify(status)

    @app.route('/robot/diagnose/<string:robot_id>', methods=['POST'])
    def diagnose_route(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден.'}), 404
        msg = robot.self_diagnose()
        if msg:
            return jsonify({'message': msg})
        return jsonify({'message': 'ОК'})

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return jsonify({'status': e.code, 'name': e.name}), e.code

    @app.route('/robot/start_move_to_shelf/<string:robot_id>', methods=['POST'])
    def start_move_to_shelf_route(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден.'}), 404
        route_data = wms.routes.get(robot.id)
        if not route_data:
            return jsonify({'error': 'Для робота нет маршрута в WMS.'}), 404
        orch = ccs.orchestrator(robot.id)
        route, distances = orch.prepare_shelf_route(route_data)
        notify_task(robot_id, 'move_to_shelf', dict(route_data))
        threading.Thread(
            target=orch.move_to_shelf,
            args=(route, distances),
            daemon=False,
        ).start()
        return jsonify({'message': 'Задача запущена', 'task_id': robot_id}), 202

    @app.route('/robot/start_grab_shelf/<string:robot_id>', methods=['POST'])
    def start_grab_shelf(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        orch = ccs.orchestrator(robot.id)
        notify_task(robot_id, 'grab_shelf', wms.routes.get(robot.id, {}))
        threading.Thread(target=orch.grab_shelf, daemon=False).start()
        return jsonify({'message': 'Задача запущена', 'task_id': robot_id}), 202

    @app.route('/robot/start_move_to_station/<string:robot_id>', methods=['POST'])
    def start_move_to_station_route(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        route_data = wms.routes.get(robot.id)
        if not route_data:
            return jsonify({'error': 'Для робота нет маршрута в WMS'}), 404
        orch = ccs.orchestrator(robot.id)
        route, distances = orch.prepare_station_route(route_data)
        notify_task(robot_id, 'move_to_station', dict(route_data))
        threading.Thread(
            target=orch.move_to_station,
            args=(route, distances),
            daemon=False,
        ).start()
        return jsonify({'message': 'Задача запущена', 'task_id': robot_id}), 202

    @app.route('/robot/start_drop_shelf/<string:robot_id>', methods=['POST'])
    def start_drop_shelf(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        orch = ccs.orchestrator(robot.id)
        notify_task(robot_id, 'drop_shelf', wms.routes.get(robot.id, {}))
        threading.Thread(target=orch.drop_shelf, daemon=False).start()
        return jsonify({'message': 'Задача запущена', 'task_id': robot_id}), 202

    @app.route('/robot/task_result/<string:robot_id>', methods=['GET'])
    def get_task_result(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        if not robot.task_done:
            return jsonify({'status': 'running'}), 200
        return jsonify({'status': 'done', 'message': robot.task_message}), 200

    # --- тестовые эндпоинты ---
    @app.route('/test/set_avoid/<string:robot_id>/<int:avoid>', methods=['POST'])
    def test_set_avoid(robot_id, avoid):
        robot = _robot(robot_id)
        if robot:
            robot.obstacle_distance_avoidance = avoid
            robot.lidar_control._threshold = avoid
        return jsonify({})

    @app.route('/test/set_battery/<string:robot_id>/<int:battery>', methods=['POST'])
    def test_set_battery(robot_id, battery):
        robot = _robot(robot_id)
        if robot:
            robot.battery_percent = battery
        return jsonify({})

    @app.route('/test/clear_route/<string:robot_id>', methods=['POST'])
    def test_clear_route(robot_id):
        wms.routes.pop(robot_id, None)
        return jsonify({})

    @app.route('/test/set_coordinates/<string:robot_id>/<string:coord>', methods=['POST'])
    def test_set_coordinates(robot_id, coord):
        robot = _robot(robot_id)
        if robot:
            robot.coordinates_qr = coord
        return jsonify({})

    @app.route('/test/set_obstacle_distance/<string:robot_id>/<int:distance>', methods=['POST'])
    def test_set_obstacle_distance(robot_id, distance):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Robot not found'}), 404
        robot.obstacle_distance = distance
        return jsonify({'status': 'ok'})

    @app.route('/test/set_shelf_distances/<string:robot_id>', methods=['POST'])
    def test_set_shelf_distances(robot_id):
        data = request.get_json() or {}
        wms.routes.setdefault(robot_id, {})
        if data.get('distances_to_shelf') is not None:
            wms.routes[robot_id]['distances_to_shelf'] = data['distances_to_shelf']
        return jsonify({'status': 'ok'})

    @app.route('/test/set_station_distances/<string:robot_id>', methods=['POST'])
    def test_set_station_distances(robot_id):
        data = request.get_json() or {}
        wms.routes.setdefault(robot_id, {})
        if data.get('distances_to_station') is not None:
            wms.routes[robot_id]['distances_to_station'] = data['distances_to_station']
        return jsonify({'status': 'ok'})

    @app.route('/test/set_route_to_shelf/<string:robot_id>', methods=['POST'])
    def test_set_route_to_shelf(robot_id):
        data = request.get_json() or {}
        wms.routes.setdefault(robot_id, {})
        if data.get('route_to_shelf') is not None:
            wms.routes[robot_id]['route_to_shelf'] = data['route_to_shelf']
        return jsonify({'status': 'ok'})

    @app.route('/test/set_route_to_station/<string:robot_id>', methods=['POST'])
    def test_set_route_to_station(robot_id):
        data = request.get_json() or {}
        wms.routes.setdefault(robot_id, {})
        if data.get('route_to_station') is not None:
            wms.routes[robot_id]['route_to_station'] = data['route_to_station']
        return jsonify({'status': 'ok'})

    @app.route('/test/reset_robot/<string:robot_id>', methods=['POST'])
    def test_reset_robot(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        avoid = robot.obstacle_distance_avoidance
        robot.reset()
        robot.obstacle_distance_avoidance = avoid
        robot.lidar_control._threshold = avoid
        wms.routes.pop(robot_id, None)
        return jsonify({
            'status': 'ok',
            'message': f'Робот {robot_id} сброшен до нулевого состояния',
        })

    @app.route('/test/check_robot_obstacles/<string:robot_id>', methods=['POST'])
    def test_check_robot_obstacles(robot_id):
        route_data = wms.routes.get(robot_id, {})
        return jsonify({
            'status': 'ok',
            'distances_to_shelf': route_data.get('distances_to_shelf', []),
            'distances_to_station': route_data.get('distances_to_station', []),
        })

    @app.route('/test/check_robot_routes/<string:robot_id>', methods=['POST'])
    def test_check_robot_routes(robot_id):
        route_data = wms.routes.get(robot_id, {})
        return jsonify({
            'status': 'ok',
            'route_to_shelf': route_data.get('route_to_shelf', []),
            'route_to_station': route_data.get('route_to_station', []),
        })

    @app.route('/test/hack_robot/<string:robot_id>', methods=['POST'])
    def test_hack_robot(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        robot.hacked = True
        return jsonify({'status': 'ok'})

    @app.route('/test/break_robot/<string:robot_id>', methods=['POST'])
    def test_break_robot(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        robot.something_broken = True
        return jsonify({'status': 'ok'})

    @app.route('/test/grab_weak/<string:robot_id>', methods=['POST'])
    def test_grab_weak_robot(robot_id):
        robot = _robot(robot_id)
        if not robot:
            return jsonify({'error': 'Робот не найден'}), 404
        robot.cargo_grip.set_weak_grip()
        return jsonify({'status': 'ok'})

    def run():
        app.run(host=host, port=port, debug=False, use_reloader=False)

    app.run_server = run
    return app
