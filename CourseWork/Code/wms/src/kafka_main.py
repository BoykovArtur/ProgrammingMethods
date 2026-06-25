import os
import time

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from multiprocessing import Queue

from src.api_kafka import start_web
from src.consumer import start_consumer
from src.producer import start_producer


MODULE_NAME = os.getenv('MODULE_NAME', 'wms')


def main():
    print(f'[DEBUG] {MODULE_NAME} started...')

    parser = ArgumentParser()
    parser.add_argument('config_file', type=FileType('r'))
    parser.add_argument('--reset', action='store_true')
    args = parser.parse_args()

    import sys
    sys.path.insert(0, '/shared')
    from kafka_config import load_kafka_configs

    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    consumer_config, producer_config = load_kafka_configs(config_parser, MODULE_NAME)

    requests_queue = Queue()
    start_web(requests_queue)
    start_consumer(args, consumer_config)
    start_producer(args, producer_config, requests_queue)

    while True:
        time.sleep(3600)
