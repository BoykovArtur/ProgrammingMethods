"""Публикация событий в Kafka (топик monitor) из drone/WMS."""

import json
import os
from uuid import uuid4

_producer = None
_enabled = os.getenv('KAFKA_ENABLED', '1') != '0'


def _get_producer():
    global _producer
    if _producer is None:
        from confluent_kafka import Producer
        bootstrap = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'broker:9092')
        _producer = Producer({'bootstrap.servers': bootstrap})
    return _producer


def publish_to_monitor(event_details: dict) -> str | None:
    """Отправить событие в monitor. Возвращает id события или None при ошибке."""
    if not _enabled:
        return None

    event_details = dict(event_details)
    event_id = event_details.get('id') or str(uuid4())
    event_details['id'] = event_id

    try:
        producer = _get_producer()

        def callback(err, msg):
            if err:
                print(f'[kafka] publish failed (id={event_id}): {err}')
            else:
                src = event_details.get('source', '?')
                dst = event_details.get('deliver_to', '?')
                op = event_details.get('operation', '?')
                print(
                    f'[kafka] -> monitor: {src}->{dst}: {op} (id={event_id})'
                )

        producer.produce(
            'monitor',
            json.dumps(event_details, ensure_ascii=False),
            event_id,
            callback=callback,
        )
        producer.poll(0)
        producer.flush(5)
        return event_id
    except Exception as exc:
        print(f'[kafka] publish skipped (id={event_id}): {exc}')
        return None


def notify_task(robot_id: str, task_operation: str, route_data: dict | None = None):
    """Запустить цепочку модулей через WMS -> communication -> ..."""
    data = {
        'robot_id': robot_id,
        'task_operation': task_operation,
        'route_data': route_data or {},
        'next_operation': 'begin_task',
    }
    publish_to_monitor({
        'source': 'wms',
        'deliver_to': 'communication',
        'operation': 'receive_task',
        'data': data,
    })
