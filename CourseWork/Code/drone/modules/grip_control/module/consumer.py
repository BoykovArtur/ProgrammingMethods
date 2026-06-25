import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_orchestrator(id, details):
    details["deliver_to"] = "delivery-orchestrator"
    proceed_to_deliver(id, details)


def send_to_cargo_grip_control(id, details, operation):
    details["deliver_to"] = "cargo-grip-control"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Управление захватом: передаёт команды в подсистему захвата груза."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation in ("grab", "drop"):
        print(f"[grip-control] Delegating {operation} to cargo-grip-control")
        return send_to_cargo_grip_control(id, details, operation)

    if operation == "grab_done":
        details["data"] = {
            "grab_result": data.get("grab_result", "Стеллаж успешно захвачен"),
            "success": data.get("success", True),
        }
        details["operation"] = "grab_complete"
        return send_to_orchestrator(id, details)

    if operation == "drop_done":
        details["data"] = {
            "drop_result": data.get("drop_result", "Стеллаж успешно опущен"),
            "success": data.get("success", True),
        }
        details["operation"] = "drop_complete"
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
