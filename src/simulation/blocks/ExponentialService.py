from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta


class ExponentialService(SimBlockInterface):
    """Rappresenta un blocco di servizio che utilizza un tempo di servizio esponenziale.
    Questo blocco gestisce una coda di persone e fornisce un servizio con un tempo di attesa basato su una distribuzione esponenziale.
    """
    def __init__(self, name, serviceRate, nextBlock:SimBlockInterface):
        """Inizializza un nuovo blocco di servizio esponenziale.
        
        Args:
            name (str): Il nome del blocco di servizio.
            serviceRate (float): Il tasso di servizio, che determina la media del tempo di servizio.
            nextBlock (SimBlockInterface): Il blocco successivo nella catena di servizi.
        """
        self.name = name
        self.serviceRate = serviceRate
        self.queueLenght = 0
        self.queue=[]
        self.working=None
        self.nextBlock = nextBlock

    def getServiceTime(self,time:datetime)->datetime:
        """Calcola il tempo di servizio esponenziale a partire da un timestamp specificato.
        
        Args:
            time (datetime): Il timestamp di inizio del servizio.   
        
        Returns:
            datetime: Il timestamp di fine del servizio, calcolato aggiungendo un tempo esponenziale al timestamp di inizio.
        """
        exp= rvgs.Exponential(1/self.serviceRate)
        return time + timedelta(seconds=exp)
    

    def get_service_name(self) -> str:
        """Restituisce il nome del servizio.
        
        Returns:
            str: Il nome del servizio associato a questo blocco.
        """
        return self.name
    
    def get_serviceRate(self) -> float:
        """Restituisce il tasso di servizio.
        
        Returns:
            float: Il tasso di servizio, che determina la media del tempo di servizio.
        """
        return self.serviceRate    
    
    def putInQueue(self,person: Person,timestamp: datetime) ->list[Event]:
        """Aggiunge una persona alla coda del blocco di servizio.
        Se il blocco è vuoto, inizia il servizio immediatamente, chiamando putNextState e creando quindi un evento.
        se la cosa è piena, la persona viene semplicemente aggiunta alla coda, e non si crea nessun evento.
        Inoltre per ogni persona aggiunta alla coda, viene creato un NormalState che rappresenta lo stato della persona nella coda.
        
        Args:
            person (Person): La persona da aggiungere alla coda.
            timestamp (datetime): Il timestamp in cui la persona entra nella coda.
        
        Returns:
            list[Event]: Una lista di eventi da processare, vuota se non ci sono eventi da gestire.
        """
        state=NormalState(self.name, timestamp, self.queueLenght)
        self.queueLenght += 1
        self.queue.append(person)
        person.append_state(state)
        if self.working is None:
            events = self.putNextEvenet(timestamp)
            return events if events else []
        return []

    def putNextEvenet(self,exitQueueTime) -> list[Event]:
        """Controlla se ci sono persone in coda e, se il blocco di servizio è vuoto, inizia il servizio della prima persona in coda.
        Se il blocco è vuoto, crea un evento che rappresenta l'inizio del servizio della persona in coda.
        
        Args:
            exitQueueTime (datetime): Il timestamp in cui la persona esce dalla coda.
        Returns:
            list[Event]: Una lista di eventi da processare, che contiene l'evento di inizio del servizio se il blocco era vuoto.
        """
        if len(self.queue) == 0:
            return []
        if self.working is None:
            self.working=self.queue.pop(0)
            self.working.get_last_state().service_start_time = exitQueueTime
            self.queueLenght -= 1
            self.working.get_last_state().service_end_time = self.getServiceTime(exitQueueTime)
            return [Event(self.working.get_last_state().service_end_time,  self.name,self.working, "queue_empty_put_to_work", self.serveNext)]
        return []

    def serveNext(self)->list[Event]:
        """Gestisce il completamento del servizio della persona attualmente in lavorazione.
        Se ci sono persone in coda, crea un evento per la prossima persona da elaborare.
        Se ha elaborato qualcuno lo passa al blocco successivo e se riceve un evento lo aggiunge alla lista degli eventi da ritornare.
        
        Returns:
            list[Event]: Una lista di eventi da processare, che contiene l'evento di inizio del servizio della prossima persona in coda se presente.
        """
        if not self.working:
            return []
        serving=self.working
        self.working = None
        endTime = serving.get_last_state().service_end_time
        events=[]
        if self.queue:
            event = self.putNextEvenet(endTime)
            if event:
                events.extend(event)
        event=self.nextBlock.putInQueue(serving, endTime)
        if event:
            events.extend(event)
        return events


