FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /wms

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y librdkafka-dev gcc \
    && rm -rf /var/lib/apt/lists/*
RUN addgroup --system wms_user && adduser --system --group wms_user

COPY config/requirements.txt config/requirements.txt
RUN python -m venv venv
RUN venv/bin/python -m pip install -U pip
RUN venv/bin/pip install -r config/requirements.txt

COPY . .

RUN chown -R wms_user /wms
USER wms_user

EXPOSE 8001

CMD ["venv/bin/python", "start_kafka.py", "/shared/config.ini"]
