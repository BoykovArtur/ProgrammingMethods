SHELL := bash

KAFKA_TOPICS := monitor \
				wms communication \
				encryption-decryption \
				task-processing \
				delivery-orchestrator \
				navigation \
				emergency-braking \
				grip-control \
				movement-system \
				cameras qr-recognition \
				qr-validation \
				lidars lidar-control \
				cargo-grip-control \
				manipulators \
				charging-controller \
				charge-state-control \
				self-diagnostic

IMAGES := monitor wms drone communication encryption task_processing \
		  delivery_orchestrator navigation emergency_braking grip_control \
		  movement cameras qr_recognition qr_validation lidars \
		  lidar_status_control cargo_grip_control manipulators \
		  charging_controller charge_state_control self_diagnostic

SLEEP_TIME := 20

dev_install:
	python3 -m venv .venv
	.venv/bin/python -m pip install -U pip
	.venv/bin/pip install -r requirements.txt

remove_kafka:
	-docker stop zookeeper broker 2>/dev/null
	-docker rm zookeeper broker 2>/dev/null

all: remove_kafka
	docker compose down
	docker compose up --build -d

logs:
	docker compose logs -f --tail 200

test_security:
	python3 tests/test_policies.py

test:
	python3 -m pytest tests/test_robots.py -v

clean:
	docker compose down
	@for IMAGE in $(IMAGES); do \
		docker rmi $$IMAGE 2>/dev/null || true; \
	done
