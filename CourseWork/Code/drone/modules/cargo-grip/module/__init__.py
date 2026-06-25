import os
import time

MODULE_NAME = os.getenv('MODULE_NAME', 'cargo-grip')


def main():
    print(f'[DEBUG] {MODULE_NAME} module ready')
    while True:
        time.sleep(3600)
