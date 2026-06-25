import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from src.wms_subsystem import wms


MODULE_NAME = os.getenv('MODULE_NAME')


def handle_event(event_id, details_str):
    details = json.loads(details_str)

    source = details.get('source')
    operation = details.get('operation')
    data = details.get('data') or {}

    print(
        f"[info] WMS event {event_id}, {source}->{details.get('deliver_to')}: "
        f"{operation}"
    )

    if operation in ('telemetry', 'send_telemetry', 'send_status'):
        robot_id = data.get('robot_id') or details.get('robot_id')
        status = data.get('status', data)
        diagnosis = data.get('diagnosis')
        wms.receive_telemetry(robot_id, status, diagnosis)
        return

    if operation in ('security_alert', 'send_alert'):
        robot_id = data.get('robot_id') or details.get('robot_id')
        alert_type = data.get('alert_type', operation)
        status = data.get('status', {})
        wms.receive_security_alert(robot_id, alert_type, status)
        return

    print(f"[warn] Unknown operation in WMS: {operation}")


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
                continue
            if msg.error():
                print(f"[error] {msg.error()}")
            else:
                try:
                    event_id = msg.key().decode('utf-8')
                    details_str = msg.value().decode('utf-8')
                    handle_event(event_id, details_str)
                except Exception as e:
                    print(f"[error] Malformed event on {topic}: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


def start_consumer(args, config):
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()
