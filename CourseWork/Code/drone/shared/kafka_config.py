"""Load Kafka client configs from config.ini (consumer vs producer)."""

CONSUMER_ONLY_KEYS = frozenset({"group.id", "auto.offset.reset"})


def load_kafka_configs(config_parser, module_name):
    default = dict(config_parser["default"])
    consumer = {**default, **dict(config_parser[module_name])}
    producer = {
        key: value for key, value in default.items()
        if key not in CONSUMER_ONLY_KEYS
    }
    return consumer, producer
