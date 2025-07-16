from abc import ABC, abstractmethod

# Idea iniziale per sta classe: modulo incaricato di autenticare un utente (con tentativi, timeout, blacklist)

class Authenticator(ABC):
    @abstractmethod
    def authenticate(self, user_id: str) -> bool: pass
