# wms_server.py
from flask import Flask, request, jsonify
from wms import wms

app = Flask(__name__)

@app.route('/telemetry/<robot_id>', methods=['POST'])
def telemetry_endpoint(robot_id):
    """Прием телеметрии от роботов"""
    data = request.json
    status = data.get('status', {})
    diagnosis = data.get('diagnosis')
    
    result = wms.receive_telemetry(robot_id, status, diagnosis)
    return jsonify(result)

@app.route('/wms/statistics/<robot_id>', methods=['GET'])
def get_robot_stats(robot_id):
    """Получить статистику конкретного робота"""
    stats = wms.get_robot_statistics(robot_id)
    if not stats:
        return jsonify({"error": "Робот не найден"}), 404
    return jsonify(stats)

@app.route('/wms/statistics/all', methods=['GET'])
def get_all_stats():
    """Получить статистику всех роботов"""
    return jsonify(wms.get_all_statistics())

@app.route('/wms/telemetry/<robot_id>', methods=['GET'])
def get_telemetry(robot_id):
    """Получить историю телеметрии робота"""
    history = wms.get_telemetry_history(robot_id)
    return jsonify(history[-100:])  # последние 100 записей

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)