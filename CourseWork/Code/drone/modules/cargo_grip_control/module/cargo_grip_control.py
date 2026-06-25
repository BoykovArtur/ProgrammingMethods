class CargoGripControl:
    """Контроль захвата груза."""

    def __init__(self, state):
        self.state = state
        self._weak = False

    def set_weak_grip(self):
        self._weak = True

    def is_weak(self):
        return self._weak
