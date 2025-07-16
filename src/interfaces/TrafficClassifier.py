from abc import ABC, abstractmethod

# Idea iniziale per sta classe: riconoscere traffico normale vs DDoS

class TrafficClassifier(ABC):
    @abstractmethod
    def classify(self, packet: dict) -> str:  # es: 'normal', 'sospetto', 'ddos'
        pass
