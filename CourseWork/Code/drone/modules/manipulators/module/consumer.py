import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_cargo_grip_control(id, details):
    details["deliver_to"] = "cargo-grip-control"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Захват и опускание стеллажа манипуляторами."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    shelf_held = data.get("shelf_held", False)
    grip_secure = data.get("grip_secure", True)

    if operation == "grab":
        if shelf_held:
            result = "Робот уже держит стеллаж"
            success = False
        else:
            result = "Робот закрепил стеллаж"
            success = True
            shelf_held = True
            grip_secure = True

        details["data"] = {
            "grab_result": result,
            "success": success,
            "shelf_held": shelf_held,
            "grip_secure": grip_secure,
        }
        details["operation"] = "manipulator_grab_done"
        return send_to_cargo_grip_control(id, details)

    if operation == "drop":
        if shelf_held and grip_secure:
            result = "Робот отпустил стеллаж"
            success = True
            shelf_held = False
        elif not grip_secure:
            result = "Робот закрепил стеллаж"
            success = True
            grip_secure = True
        else:
            result = "Робот не держит стеллаж"
            success = False

        details["data"] = {
            "drop_result": result,
            "success": success,
            "shelf_held": shelf_held,
            "grip_secure": grip_secure,
        }
        details["operation"] = "manipulator_drop_done"
        return send_to_cargo_grip_control(id, details)


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
