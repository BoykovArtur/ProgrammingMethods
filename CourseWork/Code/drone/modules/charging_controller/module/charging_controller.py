class ChargingController:
    """Управление процессом зарядки."""

    def __init__(self, state):
        self.state = state

    def start_charge(self):
        self.state.is_charging = True
        return 'Зарядка начата'

    def stop_charge(self):
        self.state.is_charging = False
        return 'Зарядка остановлена'
