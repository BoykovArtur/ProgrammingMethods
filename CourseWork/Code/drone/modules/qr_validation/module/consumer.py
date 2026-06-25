import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")

POSITION_TOLERANCE = 0.5


def send_to_navigation(id, details):
    details["deliver_to"] = "navigation"
    proceed_to_deliver(id, details)


def send_to_self_diagnostic(id, details):
    details["deliver_to"] = "self-diagnostic"
    details["operation"] = "report_qr_status"
    proceed_to_deliver(id, details)


def send_to_emergency(id, details):
    details["deliver_to"] = "emergency-braking"
    details["operation"] = "emergency_stop"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Сверка QR-кодов с данными навигации."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "provide_expected_position":
        details["data"]["awaiting_recognition"] = True
        return

    if operation == "validate_qr":
        qr_code = data.get("qr_code", "")
        detected = data.get("position", {})
        route_context = data.get("route_context", {})
        expected = (
            data.get("expected_position")
            or route_context.get("route_data", {}).get("expected_position")
            or detected
        )

        dx = abs(detected.get("x", 0) - expected.get("x", 0))
        dy = abs(detected.get("y", 0) - expected.get("y", 0))
        validated = dx <= POSITION_TOLERANCE and dy <= POSITION_TOLERANCE

        print(f"[qr-validation] QR {qr_code}: validated={validated}")

        details["data"] = {
            "qr_code": qr_code,
            "position": detected,
            "expected_position": expected,
            "validated": validated,
            "route_context": route_context,
            "message": f"QR {'OK' if validated else 'MISMATCH'}",
        }
        details["operation"] = "qr_position_validated"
        send_to_self_diagnostic(id, dict(details))

        if not validated:
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
