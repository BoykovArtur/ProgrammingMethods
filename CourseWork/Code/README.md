# Дрон-грузчик

| Сущность | Порт | Описание |
|----------|------|----------|
| **`drone/`** | 8000 | API роботов |
| **`wms/`** | 8001 | СУС (HTTP) |
| **`tests/`** | — | Тесты |

---

## Запуск через Docker

### 1. Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) установлен и **запущен** (иконка в трее без ошибок)

### 2. Подготовка (один раз)

Откройте PowerShell в корне проекта:

```powershell
cd "c:\new_architecture — копия"

python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
```

> Зависимости в `.venv` нужны для **локальных тестов** (`pytest`). Docker собирает свои образы сам.

### 3. Сборка и запуск

```powershell
docker compose up --build -d
```

**Первый запуск** может занять **10–20 минут** (скачивание Kafka, установка `gcc`, `librdkafka`).

### 4. Проверка, что контейнеры работают

```powershell
docker compose ps
```

Все сервисы должны быть **`Up`**, у `drone` и `wms` — порты `8000` и `8001`:

```
NAME        STATUS          PORTS
drone       Up ...          0.0.0.0:8000->8000/tcp
wms         Up ...          0.0.0.0:8001->8001/tcp
monitor     Up ...
broker      Up ...
zookeeper   Up ...
```

**Если у `drone` статус `Exited` — сервер не запустился.** Смотрите логи:

```powershell
docker compose logs drone --tail 50
```

### 5. Проверка API

```powershell
curl http://localhost:8000/robot/status/all
curl http://localhost:8001/wms/statistics/all
```

Ожидается JSON со списком роботов `wr-01`, `wr-02`.

### 6. Логи (если что-то не работает)

```powershell
docker compose logs -f --tail 100
```

Только drone:

```powershell
docker compose logs drone -f
```

### 7. Остановка

```powershell
docker compose down
```

Полная очистка с образами:

```powershell
docker compose down
docker rmi drone wms monitor
```

---

## Запуск локально (без Docker)

**Терминал 1 — WMS:**

```powershell
cd wms
python start.py
```

**Терминал 2 — Drone:**

```powershell
cd drone
$env:PYTHONPATH = ".;shared;..\wms"
$env:MANAGMENT_URL = "http://localhost:8001"
python start.py
```

---

## Тесты

**Политики** (серверы не нужны):

```powershell
python tests/test_policies.py
```

**Сценарии роботов** (drone должен быть на :8000):

```powershell
python -m pytest tests/test_robots.py -v
```

---

## Частые проблемы

| Проблема | Решение |
|----------|---------|
| `curl: Failed to connect to localhost:8000` | `docker compose ps` — если `drone` = `Exited`, смотрите `docker compose logs drone` |
| `dockerDesktopLinuxEngine` недоступен | Запустите Docker Desktop |
| Долгая первая сборка | Нормально; повторный `docker compose up -d` без `--build` быстрый |
| Порт занят | `docker compose down`, закройте другой процесс на 8000/8001 |

---

## Пересборка после изменения кода

```powershell
docker compose up --build -d
docker compose ps
curl http://localhost:8000/robot/status/all
```
