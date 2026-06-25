import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_qr_validation(id, details):
    details["deliver_to"] = "qr-validation"
    details["operation"] = "validate_qr"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Анализ изображения и определение положения по QR-кодам."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "recognize_qr":
        image_id = data.get("image_id", "unknown")
        qr_code = data.get("expected_qr", "QR-SHELF-001")
        confidence = data.get("confidence", 0.88)

        print(f"[qr-recognition] Recognized {qr_code} from {image_id}")

        route_context = data.get("route_context", {})
        details["data"] = {
            "image_id": image_id,
            "qr_code": qr_code,
            "position": {
                "x": data.get("x", 10.5),
                "y": data.get("y", 20.0),
                "z": data.get("z", 0.0),
            },
            "confidence": confidence,
            "recognized": True,
            "route_context": route_context,
            "expected_position": data.get("expected_position", {}),
        }
        return send_to_qr_validation(id, details)


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
