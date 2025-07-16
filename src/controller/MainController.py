import sys
import os

# Aggiungi la directory padre al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from implementations.SimpleAuthenticator import SimpleAuthenticator
from implementations.DummyDeclarationValidator import DummyDeclarationValidator
from implementations.RuleBasedTrafficClassifier import RuleBasedTrafficClassifier
from implementations.FIFO_LoadBalancer import FIFO_LoadBalancer
from implementations.FIFOQueue import FIFOQueue

class MainController:
    def __init__(self):
        self.authenticator = SimpleAuthenticator()
        self.validator = DummyDeclarationValidator()
        self.classifier = RuleBasedTrafficClassifier()
        self.load_balancer = FIFO_LoadBalancer()
        self.queue = FIFOQueue(distribution_type="exponential")

    def process_request(self, request: dict) -> dict:
        packet_type = self.classifier.classify(request)
        if packet_type == "ddos":
            return {"status": "rejected", "reason": "DDoS detected"}

        authenticated = self.authenticator.authenticate(request.get("user_id", ""))
        if not authenticated:
            return {"status": "rejected", "reason": "authentication failed"}

        valid = self.validator.validate(request.get("declaration", {}))
        if not valid:
            return {"status": "rejected", "reason": "invalid declaration data"}

        priority = self.load_balancer.assign_priority(request)
        self.queue.enqueue({
            "request": request,
            "priority": priority
        })

        return {
            "status": "queued",
            "queue_size": self.queue.size(),
            "distribution": self.queue.distribution()
        }

    def next_request(self):
        if self.queue.is_empty():
            return None
        return self.queue.dequeue()


# Esecuzione di esempio
if __name__ == "__main__":
    controller = MainController()

    test_requests = [
        {
            "user_id": "AAA001",
            "declaration": {"codice_fiscale": "AAA111"},
            "size": 500,
            "sospetto": False
        },
        {
            "user_id": "BBB002",
            "declaration": {"codice_fiscale": "BBB222"},
            "size": 1500,
            "sospetto": False
        },
        {
            "user_id": "CCC003",
            "declaration": {"codice_fiscale": "CCC333"},
            "size": 300,
            "sospetto": True
        },
        {
            "user_id": "DDD004",
            "declaration": {},  # dichiarazione mancante
            "size": 400,
            "sospetto": False
        },
        {
            "user_id": "EEE005",
            "declaration": {"codice_fiscale": "EEE555"},
            "size": 800,
            "sospetto": False
        }
    ]

    print("\n📩 Invio richieste:")
    for i, req in enumerate(test_requests):
        result = controller.process_request(req)
        print(f"[{i+1}] {req['user_id']} → {result}")

    print("\n📦 Servizio delle richieste in coda (FIFO):")
    while not controller.queue.is_empty():
        next_item = controller.next_request()
        print(f"➡️ Servendo: {next_item['request']['user_id']} con priorità {next_item['priority']}")
