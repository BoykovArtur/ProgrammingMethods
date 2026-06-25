import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")

LOW_BATTERY_THRESHOLD = 10
FAST_DRAIN_THRESHOLD = 5


def send_to_emergency(id, details):
    details["deliver_to"] = "emergency-braking"
    details["operation"] = "emergency_stop"
    proceed_to_deliver(id, details)


def send_to_self_diagnostic(id, details):
    details["deliver_to"] = "self-diagnostic"
    details["operation"] = "report_battery_status"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Валидация состояния батареи."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "update_battery_level":
        battery_percent = data.get("battery_percent", 100)
        is_low = battery_percent < LOW_BATTERY_THRESHOLD
        details["data"] = {
            "battery_percent": battery_percent,
            "is_low": is_low,
        }
        send_to_self_diagnostic(id, dict(details))
        if is_low:
            details["data"]["message"] = "Критически низкий заряд"
            return send_to_emergency(id, details)
        return

    if operation == "drain_battery":
        drain_amount = data.get("amount", 1)
        current_level = data.get("current_level", 100)
        new_level = max(0, current_level - drain_amount)
        is_low = new_level < LOW_BATTERY_THRESHOLD
        fast_drain = drain_amount >= FAST_DRAIN_THRESHOLD

        details["data"] = {
            "battery_percent": new_level,
            "is_low": is_low,
            "fast_drain": fast_drain,
            "needs_charge": is_low,
        }
        send_to_self_diagnostic(id, dict(details))

        if fast_drain or is_low:
            details["data"]["message"] = "Аномальный разряд батареи"
            return send_to_emergency(id, details)
        return

    if operation == "check_battery":
        current_level = data.get("current_level", 100)
        is_low = current_level < LOW_BATTERY_THRESHOLD
        details["data"] = {
            "battery_percent": current_level,
            "is_low": is_low,
            "needs_charge": is_low,
        }
        send_to_self_diagnostic(id, dict(details))
        if is_low:
            details["data"]["message"] = "Требуется подзарядка на базе"
            return send_to_emergency(id, details)
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
