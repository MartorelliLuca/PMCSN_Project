from desPython import rng,rngs,rvgs
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime
from datetime import timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.ExponentialService import ExponentialService
from simulation.blocks.StartBlock import StartBlock

class SimulationEngine:
    """Gestisce l'esecuzione della simulazione, orchestrando i blocchi di servizio e gli eventi.
    Inizializza i blocchi di partenza e di fine, gestisce la coda degli eventi e processa gli eventi in ordine temporale.
    """
    def __init__(self, toSIm=10):
        """Inizializza il motore di simulazione con i blocchi di partenza e fine.
        
        Args:
            toSIm (int): Numero di persone da generare nella simulazione.
        """
        self.event_queue = EventQueue()
        persons = []
        start_timestamp= datetime(2023, 10, 1, 0, 0, 0) #inio della simulazione
        times=[]
        # --------------------- inizio costruzione blocchi ---------------------
        # Crea il blocco finale che raccoglie i risultati della simulazione.
        endBlock = EndBlock()
        # Crea il blocco di servizio esponenziale che gestisce il tempo di servizio delle persone.
        exponentialService = ExponentialService("ExponentialService", 5, endBlock)
        # Crea il blocco di partenza che genera le persone e avvia il processo di simulazione.
        startingBlock = StartBlock("StartingBlock", 2, exponentialService, start_timestamp, toSIm)
        # --------------------- fine costruzione blocchi ---------------------
        # Aggiungo il primo evento alla coda per iniziare la simulazione.
        startingEvent = startingBlock.start()
        self.event_queue.push(startingEvent)
        #Simulo fino alla fine
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            event=event[0] if isinstance(event, list) else event
            #print(f"Processing event: {event}","timestamp:", event.timestamp, "serviceName:", event.serviceName, "person:", event.person.ID, "eventType:", event.eventType)
            if event.handler:
                new_events = event.handler()
                if new_events:
                    for new_event in new_events:
                        self.event_queue.push(new_event)
        # Scrive i risultati finali in formato testuale e JSON.
        endBlock.finalize()


