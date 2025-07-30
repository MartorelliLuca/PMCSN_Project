from desPython import rng,rngs,rvgs
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime, date
from datetime import timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.ExponentialService import ExponentialService
from simulation.blocks.StartBlock import StartBlock
from simulation.blocks.StartVecchio import StartVecchio 
from simulation.blocks.Evasione import Evasione
from simulation.blocks.InEsame import InEsame

from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.Instradamento import Instradamento

class SimulationEngine:
    """Gestisce l'esecuzione della simulazione, orchestrando i blocchi di servizio e gli eventi.
    Inizializza i blocchi di partenza e di fine, gestisce la coda degli eventi e processa gli eventi in ordine temporale.
    """

    
    def generateArrivalsRates(self) -> list[float]:
        """Genera un array di tassi medi di arrivo per ogni giorno tra 1 maggio e 30 settembre (inclusi).

        Returns:
            list[float]: Lista di tassi medi, uno per ciascun giorno.
        """

        start = date(2025, 5, 1)
        end = date(2025, 9, 30)
        delta = (end - start).days + 1  # incluso l'ultimo giorno

        # Genera tassi casuali (es: esponenziale con media 5 secondi)
        rates = [rvgs.Uniform(0.001,0.005) for _ in range(delta)]
        return rates

    

    def test(self, toSim):
        """Inizializza il motore di simulazione con i blocchi di partenza e fine.
        
        Args:
            toSIm (int): Numero di persone da generare nella simulazione.
        """
        self.event_queue = EventQueue()
        persons = []
        start_timestamp= datetime(2023, 10, 1, 0, 0, 0) #inio della simulazione
        times=[]
        endBlock = EndBlock()    
        inEsame = InEsame("InEsame", 2, 0.5, endBlock)
        daily_rates = self.generateArrivalsRates()


        evasione = Evasione("Evasione", 0.1,0.1, inEsame)
        autenticazione  = Autenticazione("Autenticazione", 4, 0.3, evasione)
        instradamento = Instradamento("Instradamento", 6.25, autenticazione)
        startingBlock = StartBlock("Start", nextBlock=instradamento, start_timestamp=datetime(2025, 5, 1, 0, 0), daily_rates=daily_rates)
        
        autenticazione.setInstradamento(instradamento)
        inEsame.setInstradamento(instradamento)
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






    def normal(self, toSIm=10):
        """Inizializza il motore di simulazione con i blocchi di partenza e fine.
        
        Args:
            toSIm (int): Numero di persone da generare nella simulazione.
        """
        self.event_queue = EventQueue()
        persons = []
        start_timestamp= datetime(2023, 10, 1, 0, 0, 0) #inio della simulazione
        times=[]
        endBlock = EndBlock()    
        inEsame = InEsame("InEsame", 2, 0.5, endBlock)

        evasione = Evasione("Evasione", 0.1,0.1, inEsame)
        autenticazione  = Autenticazione("Autenticazione", 4, 0.3, evasione)
        instradamento = Instradamento("Instradamento", 6.25, autenticazione)
        startingBlock = StartVecchio("StartingBlock", 5, instradamento, start_timestamp, toSIm) 
        autenticazione.setInstradamento(instradamento)
        inEsame.setInstradamento(instradamento)
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


