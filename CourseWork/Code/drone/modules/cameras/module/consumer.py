import os
import json
import threading
import time

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_qr_recognition(id, details):
    details["deliver_to"] = "qr-recognition"
    details["operation"] = "recognize_qr"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Заглушка камер: отправляет кадр в распознавание QR."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation in ("capture_image", "auto_capture", None):
        image_id = f"img_{int(time.time())}"
        print(f"[cameras] Captured stub frame {image_id}")

        details["data"] = {
            "image_id": image_id,
            "image_data": "simulated_frame",
            "expected_qr": data.get("expected_qr", "QR-SHELF-001"),
            "route_context": data.get("route_context", {}),
            "expected_position": data.get("expected_position", {}),
        }
        return send_to_qr_recognition(id, details)


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
