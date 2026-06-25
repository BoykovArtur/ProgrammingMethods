import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")

OBSTACLE_THRESHOLD = 30
LIDAR_MAX_DISTANCE = 500
LIDAR_MIN_DISTANCE = 5


def send_to_navigation(id, details):
    details["deliver_to"] = "navigation"
    proceed_to_deliver(id, details)


def send_to_emergency(id, details):
    details["deliver_to"] = "emergency-braking"
    details["operation"] = "emergency_stop"
    proceed_to_deliver(id, details)


def send_to_self_diagnostic(id, details):
    details["deliver_to"] = "self-diagnostic"
    details["operation"] = "report_lidar_status"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Проверка корректности работы лидаров."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "provide_expected_distance":
        details["data"]["awaiting_measurement"] = True
        return

    if operation == "validate_lidar":
        distance = data.get("distance", 100)
        expected = data.get("expected_distance", distance)
        route_context = data.get("route_context", {})
        tolerance = data.get("tolerance", 20)

        in_range = LIDAR_MIN_DISTANCE <= distance <= LIDAR_MAX_DISTANCE
        is_obstacle = distance < OBSTACLE_THRESHOLD
        diff = abs(distance - expected)
        validated = in_range and diff <= tolerance and not is_obstacle

        print(f"[lidar-control] distance={distance}cm validated={validated}")

        details["data"] = {
            "distance": distance,
            "expected_distance": expected,
            "is_obstacle": is_obstacle,
            "validated": validated,
            "route_context": route_context,
            "message": f"Лидар: {distance}см",
        }
        details["operation"] = "lidar_data_validated"
        send_to_self_diagnostic(id, dict(details))

        if is_obstacle or not validated:
            details["data"]["obstacle_distance"] = distance
            return send_to_emergency(id, details)

        return send_to_navigation(id, details)


def consumer_job(args, config):
    consumer = Consumer(config)

    def reset_offset(verifier_consumer, partitions):
        if not args.reset:
            return
        for p in partitions:
            p.offset = OFFSET_BEGINNING
        verifier_consumer.assign(partitions)

    topic = MODULE_NAME
    consumer.subscribe([topic], on_assign=reset_offset)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                try:
                    id = msg.key().decode('utf-8')
                    details_str = msg.value().decode('utf-8')
                    handle_event(id, details_str)
                except Exception as e:
                    print(f"[error] Malformed event received from "
                          f"topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


def start_consumer(args, config):
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()
