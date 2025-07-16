from abc import ABC, abstractmethod

class LoadBalancer(ABC):
    @abstractmethod
    def assign_priority(self, request: dict) -> int: pass