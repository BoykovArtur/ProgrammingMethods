#!/bin/bash
set -euo pipefail

TOPICS=(
  monitor
  wms
  communication
  encryption-decryption
  task-processing
  delivery-orchestrator
  navigation
  emergency-braking
  grip-control
  movement-system
  cameras
  qr-recognition
  qr-validation
  lidars
  lidar-control
  cargo-grip-control
  manipulators
  charging-controller
  charge-state-control
  self-diagnostic
)

echo "Waiting for Kafka broker..."
cub kafka-ready -b broker:9092 1 60

for topic in "${TOPICS[@]}"; do
  echo "Creating topic ${topic}"
  kafka-topics --create --if-not-exists \
    --topic "${topic}" \
    --bootstrap-server broker:9092 \
    --replication-factor 1 \
    --partitions 1
done

echo "All Kafka topics are ready"
