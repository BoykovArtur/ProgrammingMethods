LOW_BATTERY_THRESHOLD = 10


class ChargeStateControl:
    """Контроль уровня заряда батареи."""

    def __init__(self, state):
        self.state = state

    def update_level(self, battery_percent):
        self.state.battery_percent = battery_percent

    def is_low(self):
        return self.state.battery_percent < LOW_BATTERY_THRESHOLD
