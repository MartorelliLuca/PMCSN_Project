from interfaces.Authenticator import Authenticator

class SimpleAuthenticator(Authenticator):
    def __init__(self):
        self.blocked_users = {}

    def authenticate(self, user_id: str) -> bool:
        return not self.blocked_users.get(user_id, False)