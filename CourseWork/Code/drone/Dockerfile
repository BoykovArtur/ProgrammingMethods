FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY drone ./drone
COPY wms ./wms

WORKDIR /app/drone
ENV PYTHONPATH=/app/drone:/app/drone/shared:/app/wms

EXPOSE 8000

CMD ["python", "start.py"]
