class EncryptionDecryption:
    """Проверка целостности задания."""

    def __init__(self, state):
        self.state = state

    def check_compromised(self):
        if self.state.hacked:
            self.state.hacked_noticed = True
            return True
        return False
