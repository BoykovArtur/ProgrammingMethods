import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_navigation(id, details, operation):
    details["deliver_to"] = "navigation"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_emergency(id, details, operation):
    details["deliver_to"] = "emergency-braking"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_cargo_grip(id, details, operation):
    details["deliver_to"] = "cargo-grip-control"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_task_processing(id, details, operation):
    details["deliver_to"] = "task-processing"
    details["operation"] = operation
    proceed_to_deliver(id, details)


def send_to_self_diagnostic(id, details):
    details["deliver_to"] = "self-diagnostic"
    details["operation"] = "run_diagnostics"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Главный оркестратор процесса доставки."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "begin_task":
        operation = data.get("task_operation", "move_to_shelf")
        details["operation"] = operation
        print(f"[orchestrator] begin_task -> {operation}")

    if operation == "start_delivery":
        print("[orchestrator] Starting delivery...")
        send_to_self_diagnostic(id, dict(details))
        return send_to_task_processing(id, details, "begin_task")

    if operation == "move_to_shelf":
        route_data = data.get("route_data", {})
        details["data"] = {"route_data": route_data}
        return send_to_navigation(id, details, "prepare_route_to_shelf")

    if operation == "route_prepared":
        if data.get("validated"):
            return send_to_emergency(id, details, "move_forward")
        print("[orchestrator] Route validation failed")
        return send_to_emergency(id, details, "emergency_stop")

    if operation == "grab_shelf":
        return send_to_cargo_grip(id, details, "grab")

    if operation == "grab_done":
        return send_to_emergency(id, details, "move_backward")

    if operation == "move_to_station":
        route_data = data.get("route_data", {})
        details["data"] = {"route_data": route_data}
        return send_to_navigation(id, details, "prepare_route_to_station")

    if operation == "drop_shelf":
        return send_to_cargo_grip(id, details, "drop")

    if operation == "drop_done":
        return send_to_task_processing(id, details, "complete_task")

    if operation == "return_to_base":
        return send_to_emergency(id, details, "move_to_base")

    if operation == "diagnostics_report":
        print(f"[orchestrator] Diagnostics: all_ok={data.get('all_ok')}")
        if not data.get("all_ok"):
            return send_to_emergency(id, details, "emergency_stop")
        return

    if operation == "movement_done":
        print(f"[orchestrator] Movement completed: {data.get('message')}")
        return


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
