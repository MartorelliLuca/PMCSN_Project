from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta

class StartVecchio(SimBlockInterface):
    """Rappresenta un blocco di partenza che genera persone con un tempo di servizio esponenziale.
    Questo blocco inizia la simulazione generando una persona e avviando il processo di creazione degli utenti.
    Per ora è molto semplice, genero un numero di persone pari al numero di eventi che voglio generare.
    Il tasso di servizio è costante e il blocco successivo è specificato al momento della creazione.
    Ogni volta che viene generato un utente si crea un evento per generaere il successivo.
    TODO: naturalemnte questo l'ho creato solo per testare inizialmente, quindi è da cambiare.
    """
    def __init__(self, name, rate,nextBlock: SimBlockInterface,start_timestamp: datetime,toSim):
        """Inizializza un nuovo blocco di partenza.
        
        Args:
            name (str): Il nome del blocco di partenza.
            rate (float): Il tasso di servizio, che determina la media del tempo di servizio.
            nextBlock (SimBlockInterface): Il blocco successivo nella catena di servizi.
            start_timestamp (datetime): Il timestamp di inizio della simulazione.
            toSim (int): Il numero di persone da generare nella simulazione.
        """
        self.name = name
        self.next=None
        self.generated=0
        self.nextBlock = nextBlock
        self.start_timestamp = start_timestamp
        self.rate = rate
        self.toSim = toSim                                                                #tempo finale di simulazione


    def getServiceTime(self,time:datetime)->datetime:
        """Calcola il tempo di servizio esponenziale a partire da un timestamp specificato.
        
        Args:
            time (datetime): Il timestamp di inizio del servizio.   
        
        Returns:
            datetime: Il timestamp di fine del servizio, calcolato aggiungendo un tempo esponenziale al timestamp di inizio.
        """
        exp= rvgs.Exponential(1/self.rate)
        return time + timedelta(seconds=exp)
    
    def start(self):
        """Genera una nuova persona e il primo evento da cui parte il sistema.
        
        Returns:
            Event: Un evento che rappresenta l'inizio del servizio della persona generata.
        """
        self.next = Person(self.generated)
        self.generated += 1
        nextServe= self.getServiceTime(self.start_timestamp)
        state = NormalState(self.name, nextServe, 0)
        state.service_end_time = nextServe
        state.service_start_time = nextServe
        self.start_timestamp = nextServe
        self.next.set_last_state(state)
        return Event(nextServe, self.name, self.next, "generated_event", self.serveNext)

 
    def serveNext(self) -> [Event]:
        """Rappresenta l'handler del evento, aggiunge la persona alla coda del primo blocco, e genera il prossimo evento.
        
        Returns:
            list[Event]: Una lista di eventi da processare, che contiene l'evento di inizio del servizio della prossima persona in coda se presente.
        """
        if self.next is None:
            return []
        if self.generated >= self.toSim:
            return []
        
        serving = self.next
        self.next = None
        endTime = serving.get_last_state().service_end_time
        events = []
        
        if self.nextBlock:
            event = self.nextBlock.putInQueue(serving, endTime)
            if event:
                events.extend(event)
        
        # Print progress at regular intervals
        if self.generated % max(1, self.toSim // 1000) == 0:  # Print every 5%
            progress = (self.generated / self.toSim) * 100
            print(f"[{self.name}] Progress: {self.generated}/{self.toSim} ({progress:.1f}%)")
        
        if self.generated < self.toSim:
            new_event = self.start()
            if new_event:
                events.append(new_event)
        
        # Print completion message
        if self.generated >= self.toSim:
            print(f"[{self.name}] Generation complete: {self.toSim} entities generated")
        
        return events if events else []