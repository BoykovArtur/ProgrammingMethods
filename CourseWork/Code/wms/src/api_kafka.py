import os
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

from src.wms_subsystem import wms


HOST = '0.0.0.0'
PORT = int(os.getenv('MODULE_PORT', '8001'))
MODULE_NAME = os.getenv('MODULE_NAME', 'wms')

_requests_queue: multiprocessing.Queue = None

app = Flask(__name__)


def _publish_to_monitor(details):
    details['deliver_to'] = details.get('deliver_to', 'wms')
    details['source'] = MODULE_NAME
    details['id'] = details.get('id') or str(uuid4())
    if _requests_queue:
        _requests_queue.put(details)
        print(
            f"[kafka] WMS queued {details['source']}->{details['deliver_to']}: "
            f"{details.get('operation')} (id={details['id']})"
        )


@app.route('/wms/dispatch/<robot_id>', methods=['POST'])
def dispatch_task(robot_id):
    """Отправить задачу робота в шину событий (WMS -> communication -> ...)."""
    body = request.get_json(silent=True) or {}
    task_operation = body.get('task_operation', 'move_to_shelf')
    route_data = body.get('route_data')
    if route_data is None:
        route_data = wms.routes.get(robot_id, {})

    event_id = str(uuid4())
    _publish_to_monitor({
        'id': event_id,
        'deliver_to': 'communication',
        'operation': 'receive_task',
        'data': {
            'robot_id': robot_id,
            'task_operation': task_operation,
            'route_data': route_data,
            'next_operation': 'begin_task',
        },
    })
    return jsonify({
        'status': 'queued',
        'event_id': event_id,
        'robot_id': robot_id,
        'task_operation': task_operation,
    }), 202


@app.route('/telemetry/<robot_id>', methods=['POST'])
def telemetry_endpoint(robot_id):
    """HTTP fallback (без шины): прямая запись в WMS."""
    data = request.json or {}
    status = data.get('status', {})
    diagnosis = data.get('diagnosis')
    result = wms.receive_telemetry(robot_id, status, diagnosis)
    return jsonify(result)


@app.route('/wms/statistics/<robot_id>', methods=['GET'])
def get_robot_stats(robot_id):
    stats = wms.get_robot_statistics(robot_id)
    if not stats:
        return jsonify({'error': 'Робот не найден'}), 404
    return jsonify(stats)


@app.route('/wms/statistics/all', methods=['GET'])
def get_all_stats():
    return jsonify(wms.get_all_statistics())


@app.route('/wms/telemetry/<robot_id>', methods=['GET'])
def get_telemetry(robot_id):
    history = wms.get_telemetry_history(robot_id)
    return jsonify(history[-100:])


@app.route('/wms/security', methods=['GET'])
def get_security_log():
    return jsonify(wms.get_security_log())


@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({'status': e.code, 'name': e.name}), e.code


def start_web(requests_queue):
    global _requests_queue
    _requests_queue = requests_queue
    threading.Thread(
        target=lambda: app.run(
            host=HOST, port=PORT, debug=False, use_reloader=False
        )
    ).start()
