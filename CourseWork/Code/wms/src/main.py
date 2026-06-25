"""Локальный запуск WMS (как payment-system/src/main.py)."""
from src.api_kafka import app, HOST, PORT

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
