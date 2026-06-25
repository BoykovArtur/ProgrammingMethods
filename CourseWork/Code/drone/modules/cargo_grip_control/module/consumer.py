import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_manipulators(id, details, operation):
    details["deliver_to"] = "manipulators"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_self_diagnostic(id, details):
    details["deliver_to"] = "self-diagnostic"
    details["operation"] = "report_grip_status"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Контроль захвата груза."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation in ("grab", "drop"):
        data.setdefault("grip_secure", True)
        data.setdefault("shelf_held", False)
        details["data"] = data
        return send_to_manipulators(id, details, operation)

    if operation == "manipulator_grab_done":
        details["data"] = {
            "success": data.get("success", False),
            "grab_result": data.get("grab_result", ""),
            "grip_secure": data.get("grip_secure", True),
        }
        details["operation"] = "grab_done"
        send_to_self_diagnostic(id, dict(details))
        details["deliver_to"] = "delivery-orchestrator"
        return proceed_to_deliver(id, details)

    if operation == "manipulator_drop_done":
        details["data"] = {
            "success": data.get("success", False),
            "drop_result": data.get("drop_result", ""),
        }
        details["operation"] = "drop_done"
        send_to_self_diagnostic(id, dict(details))
        details["deliver_to"] = "delivery-orchestrator"
        return proceed_to_deliver(id, details)


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
