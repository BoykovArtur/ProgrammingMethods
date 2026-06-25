import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")

_reports: dict = {}


def send_to_orchestrator(id, details):
    details["deliver_to"] = "delivery-orchestrator"
    proceed_to_deliver(id, details)


def _store(event_id: str, key: str, data: dict):
    bucket = _reports.setdefault(event_id, {})
    bucket[key] = data
    return bucket


def handle_event(id, details_str):
    """Сбор отчётов валидирующих модулей."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "report_qr_status":
        _store(id, "qr", {**data, "status": "OK" if data.get("validated") else "ERROR"})
        return

    if operation == "report_lidar_status":
        _store(id, "lidar", {**data, "status": "OK" if data.get("validated") else "ERROR"})
        return

    if operation == "report_grip_status":
        _store(id, "grip", {**data, "status": "OK" if data.get("success") else "ERROR"})
        return

    if operation == "report_battery_status":
        _store(id, "battery", {**data, "status": "OK" if not data.get("is_low") else "LOW"})
        return

    if operation == "report_movement_status":
        _store(id, "movement", {**data, "status": "OK" if data.get("moved") or data.get("stopped") else "ERROR"})
        return

    if operation == "run_diagnostics":
        stored = _reports.get(id, {})
        diagnostics = {
            "qr_status": stored.get("qr", {}).get("status", "OK"),
            "lidar_status": stored.get("lidar", {}).get("status", "OK"),
            "grip_status": stored.get("grip", {}).get("status", "OK"),
            "battery_status": stored.get("battery", {}).get("status", "OK"),
            "movement_status": stored.get("movement", {}).get("status", "OK"),
            "reports": stored,
        }
        diagnostics["all_ok"] = all(
            diagnostics[k] == "OK"
            for k in ("qr_status", "lidar_status", "grip_status", "battery_status", "movement_status")
        )
        details["data"] = diagnostics
        details["operation"] = "diagnostics_report"
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
