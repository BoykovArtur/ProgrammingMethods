import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_orchestrator(id, details):
    details["deliver_to"] = "delivery-orchestrator"
    proceed_to_deliver(id, details)


def send_to_encryption(id, details, operation):
    details["deliver_to"] = "encryption-decryption"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_emergency(id, details, operation):
    details["deliver_to"] = "emergency-braking"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Обработка задания между WMS и оркестратором."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "begin_task":
        details["task_done"] = False
        details["task_message"] = None
        return send_to_orchestrator(id, details)

    if operation == "complete_task":
        details["task_done"] = True
        details["task_message"] = data.get("message", "Task completed")
        details["data"] = {
            **data,
            "next_operation": "send_status",
        }
        return send_to_encryption(id, details, "encrypt_outbound")

    if operation in ("move_forward", "move_backward", "rotate", "move_to_base"):
        print(f"[task-processing] Movement command via emergency-braking: {operation}")
        details["data"] = data
        return send_to_emergency(id, details, operation)

    if operation == "get_task_status":
        details["data"] = {
            "task_done": data.get("task_done", False),
            "task_message": data.get("task_message"),
        }
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
