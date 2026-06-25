import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_orchestrator(id, details):
    details["deliver_to"] = "delivery-orchestrator"
    proceed_to_deliver(id, details)


def send_to_qr_validation(id, details, operation):
    details["deliver_to"] = "qr-validation"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_lidar_control(id, details, operation):
    details["deliver_to"] = "lidar-control"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Координация QR и лидаров, передача данных оркестратору."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "qr_position_validated":
        pending = data.get("route_context", {}).get("pending", {})
        pending["qr"] = data
        data["route_context"]["pending"] = pending
        details["data"] = data
        return _try_finalize_route(id, details)

    if operation == "lidar_data_validated":
        pending = data.get("route_context", {}).get("pending", {})
        pending["lidar"] = data
        data["route_context"]["pending"] = pending
        details["data"] = data
        return _try_finalize_route(id, details)

    if operation in ("prepare_route_to_shelf", "prepare_route_to_station"):
        route_data = data.get("route_data", {})
        route_context = {"route_type": operation, "route_data": route_data}
        payload = {
            "route_context": route_context,
            "expected_position": route_data.get("expected_position", {}),
            "expected_qr": route_data.get("expected_qr", "QR-SHELF-001"),
            "expected_distance": route_data.get("expected_distance", 100),
        }
        details["data"] = payload
        send_to_qr_validation(id, dict(details), "provide_expected_position")
        send_to_lidar_control(id, dict(details), "provide_expected_distance")
        _trigger_sensors(id, details)
        return


def _trigger_sensors(id, details):
    """Запуск заглушек камер и лидаров (цепочка cameras->qr-recognition, lidars->lidar-control)."""
    cam = dict(details)
    cam["deliver_to"] = "cameras"
    cam["operation"] = "capture_image"
    proceed_to_deliver(id, cam)

    lid = dict(details)
    lid["deliver_to"] = "lidars"
    lid["operation"] = "measure_distance"
    proceed_to_deliver(id, lid)


def _try_finalize_route(id, details):
    route_context = details.get("data", {}).get("route_context", {})
    pending = route_context.get("pending", {})
    if not (pending.get("qr") and pending.get("lidar")):
        return

    qr_ok = pending["qr"].get("validated", False)
    lidar_ok = pending["lidar"].get("validated", False)
    route_type = route_context.get("route_type", "prepare_route_to_shelf")
    route_data = route_context.get("route_data", {})

    if route_type == "prepare_route_to_shelf":
        prepared = {
            "route_to_shelf": route_data.get("route_to_shelf", []),
            "distances_to_shelf": route_data.get("distances_to_shelf", []),
            "validated": qr_ok and lidar_ok,
        }
    else:
        prepared = {
            "route_to_station": route_data.get("route_to_station", []),
            "distances_to_station": route_data.get("distances_to_station", []),
            "validated": qr_ok and lidar_ok,
        }

    details["data"] = prepared
    details["operation"] = "route_prepared"
    return send_to_orchestrator(id, details)


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
