class SelfDiagnosticModule:
    """Самодиагностика робота."""

    def __init__(self, state, threshold=10):
        self.state = state
        self._threshold = threshold

    def run(self):
        if self.state.something_broken:
            self.state.something_broken_noticed = True
            return 'Обнаружена неисправность'
        return None
