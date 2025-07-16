from abc import ABC, abstractmethod

# Idea iniziale per sta classe: gestisce le richieste in entrata e coordina le fasi (autenticazione, validazione, ecc.)

class AccessRequestHandler(ABC):
    @abstractmethod
    def handle_request(self, request): pass
