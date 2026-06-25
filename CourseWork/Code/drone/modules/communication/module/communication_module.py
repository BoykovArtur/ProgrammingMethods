class CommunicationModule:
    """Обмен данными с WMS."""

    def send_status(self, robot_id, status):
        print(f'[communication] status from {robot_id}: {status}')

    def send_telemetry(self, robot_id, status):
        print(f'[communication] telemetry from {robot_id}')
