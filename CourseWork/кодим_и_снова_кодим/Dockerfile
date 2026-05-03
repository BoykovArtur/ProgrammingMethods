FROM python:3.12-slim

WORKDIR /src

# Устанавливаем зависимости
COPY config/requirements.txt config/requirements.txt
RUN pip install --no-cache-dir -r config/requirements.txt

# Копируем весь проект
COPY . .

# Создаем venv (опционально)
RUN python -m venv venv
RUN venv/bin/pip install --upgrade pip

# Устанавливаем зависимости в venv
RUN venv/bin/pip install -r config/requirements.txt

CMD ["venv/bin/python", "start.py"]