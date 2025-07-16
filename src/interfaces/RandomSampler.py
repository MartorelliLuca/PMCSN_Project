from abc import ABC, abstractmethod

class RandomSampler(ABC):
    @abstractmethod
    def sample(self) -> float:
        pass