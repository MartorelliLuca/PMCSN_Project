
from models.person import Person
from simulation.Event import Event
from datetime import datetime


class SimBlockInterface:
    """Interfaccia per i blocchi di simulazione.
    
    Ogni metodo deve restituire una lista di eventi (eventualmente vuota).
    Gli eventi sono strettamente azioni che la simulazione deve eseguire ad un certo timestamp, non azione fatte durante la chiamata di funzione.
    """

    def putInQueue(self, person: Person, timestamp: datetime) -> list[Event]:
        """Mette una persona in coda.
        
        Args:
            person (Person): La persona da aggiungere alla coda.
            timestamp (datetime): Il timestamp quando la persona entra in coda.
            
        Returns:
            list[Event]: Una lista di eventi generati da questa azione.
        """
        pass
    
    def putNextEvenet(self, exitQueueTime) -> list[Event]:
        """Mette la prossima persona in elaborazione.
        
        Args:
            exitQueueTime: Il tempo quando la persona esce dalla coda e inizia l'elaborazione.
            
        Returns:
            list[Event]: Una lista di eventi generati da questa azione.
        """
        pass
    
    def serveNext(self) -> list[Event]:
        """Finisce il servizio della prossima persona.
        
        Returns:
            list[Event]: Una lista di eventi generati dal completamento del servizio.
        """
        pass