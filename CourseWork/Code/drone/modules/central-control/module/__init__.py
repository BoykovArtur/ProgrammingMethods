import os
import time

MODULE_NAME = os.getenv('MODULE_NAME', 'central-control')


def main():
    print(f'[DEBUG] {MODULE_NAME} started')
    while True:
        time.sleep(3600)
