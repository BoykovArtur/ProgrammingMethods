class Manipulators:
    """Манипуляторы захвата стеллажа."""

    def __init__(self, state, cargo_grip=None):
        self.state = state
        self._cargo_grip = cargo_grip

    def grab(self):
        self.state.take_shelf = True
        self.state.grab_correctly = True
        return 'Робот закрепил стеллаж'

    def drop(self):
        if self._cargo_grip and self._cargo_grip.is_weak():
            self.state.grab_correctly = True
            return 'Робот закрепил стеллаж'
        self.state.take_shelf = False
        return 'Робот отпустил стеллаж'
