import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME: str = os.getenv("MODULE_NAME")


def send_to_movement(id, details):
    details["deliver_to"] = "movement-system"
    proceed_to_deliver(id, details)


def handle_event(id, details_str):
    """Посредник: все команды движения проходят через аварийное торможение."""
    details = json.loads(details_str)

    source: str = details.get("source")
    deliver_to: str = details.get("deliver_to")
    data: dict = details.get("data", {})
    operation: str = details.get("operation")

    print(f"[info] handling event {id}, "
          f"{source}->{deliver_to}: {operation}")

    if operation == "emergency_stop":
        print("[emergency-braking] EMERGENCY STOP")
        details["data"] = {
            "stopped": True,
            "emergency": True,
            "message": "Аварийная остановка",
        }
        details["operation"] = "stop"
        return send_to_movement(id, details)

    if operation in ("move_forward", "move_backward", "rotate", "move_to_base", "stop"):
        print(f"[emergency-braking] Forwarding movement: {operation}")
        details["operation"] = operation
        return send_to_movement(id, details)

    if operation == "check_obstacles":
        obstacle_distance = data.get("obstacle_distance", data.get("distance", 100))
        if obstacle_distance < 30:
            details["data"] = {
                "stopped": True,
                "message": "Препятствие обнаружено, остановка",
            }
            details["operation"] = "stop"
            return send_to_movement(id, details)

        details["data"] = {"cleared": True, "message": "Препятствий нет"}
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
