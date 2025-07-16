from abc import ABC, abstractmethod

# Idea iniziale per sta classe: validare i dati di dichiarazione reddituale

class DeclarationValidator(ABC):
    @abstractmethod
    def validate(self, declaration_data: dict) -> bool: pass

