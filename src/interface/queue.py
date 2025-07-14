from abc import ABC, abstractmethod

class Queue(ABC):
    @abstractmethod
    def distribution(self):
        pass
