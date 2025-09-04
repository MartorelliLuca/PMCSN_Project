from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.StateWithServiceTIme import StateWithServiceTime
from desPython import rvgs


class InValutazioneCodaPrioritaNP(SimBlockInterface):
    
    def __init__(self, name, dipendenti, pratichePerDipendente, mean, variance, successProbability):
        self.stream = 5
        self.name = name
        self.mean = mean              # media dei tempi di servizio
        self.variance = variance      # (non usata per l’esponenziale, ma la lascio per compatibilità)
        self.serversNumber = dipendenti * pratichePerDipendente
        self.accetpanceRate = successProbability

        # Code separate in base al tipo
        self.queueLenght = {
            "Diretta": 0,
            "Pesante": 0,
            "Leggera": 0
        }
        self.queue = {
            "Diretta": [],
            "Pesante": [],
            "Leggera": []
        }

        self.working = 0
        self.instradamento = None
        self.end = None


    def setInstradamento(self, instradamento: SimBlockInterface):
        """Imposta il blocco di instradamento."""
        self.instradamento = instradamento

    def setEnd(self, end: SimBlockInterface): 
        """Imposta il blocco di fine."""
        self.end = end
    

    def getServiceTime(self) -> datetime:
        """Genera un tempo di servizio da distribuzione esponenziale."""
        from desPython import rngs
        rngs.selectStream(self.stream)
        service_time = rvgs.Exponential(self.mean)  # tempo medio = self.mean
        return timedelta(seconds=service_time)

    def getServiceTimeOld(self, time: datetime) -> datetime:
        """Versione 'old' con tempo di partenza specificato."""
        from desPython import rngs
        rngs.selectStream(self.stream)
        service_time = rvgs.Exponential(self.mean)
        return time + timedelta(seconds=service_time)
    

    def getSuccess(self):
        """Determina se la pratica ha successo con probabilità self.accetpanceRate."""
        from desPython import rngs
        rngs.selectStream(self.stream + 100)
        n = rvgs.Uniform(0, 1)
        return n <= self.accetpanceRate
    
    def get_service_name(self) -> str:
        return self.name
    
    def get_serviceRate(self) -> float:
        # NB: prima usavi self.serviceRate, ma non era definito. 
        # Con distribuzione esponenziale il rate è 1/mean
        return 1 / self.mean if self.mean > 0 else 0.0
    
    
    def putInQueue(self, person: Person, timestamp: datetime) -> list[Event]:
        """Inserisce una persona nella coda corretta e, se possibile, avvia subito il servizio."""
        comingFrom = person.get_last_state().get_service_name()
        execTime = self.getServiceTime()
        queueLength = 0
        queueName = ""    

        if comingFrom == "InvioDiretto":
            queueName = "Diretta"            
        else:
            if execTime.total_seconds() > (self.mean * 1.5):
                queueName = "Pesante"
            else:
                queueName = "Leggera"

        queueLength = self.queueLenght[queueName]
        self.queueLenght[queueName] += 1
        
        state = StateWithServiceTime(self.name, timestamp, queueLength, execTime, queueName)
        self.queue[queueName].append(person)    
        person.append_state(state)
        
        if self.working < self.serversNumber:
            events = self.putNextEvent(timestamp)
            return events if events else []
        return []


    def putNextEvent(self, exitQueueTime) -> list[Event]:
        """Estrae la prossima persona dalla coda con priorità e genera un evento di fine servizio."""
        queueName = ""
        if self.queueLenght["Diretta"] > 0:
            queueName = "Diretta"
        elif self.queueLenght["Leggera"] > 0:
            queueName = "Leggera"
        elif self.queueLenght["Pesante"] > 0:
            queueName = "Pesante"
        else:
            return []
        
        if self.working < self.serversNumber:
            self.working += 1
            person = self.queue[queueName].pop(0)
            serviceTime = person.get_last_state().getServiceTime()
            person.get_last_state().service_start_time = exitQueueTime
            self.queueLenght[queueName] -= 1

            person.get_last_state().service_end_time = exitQueueTime + serviceTime
            return [Event(person.get_last_state().service_end_time, self.name, person, "queue_empty_put_to_work", self.serveNext)]
        return []


    def serveNext(self, person) -> list[Event]:
        """Gestisce la fine del servizio e instrada la persona al blocco successivo."""
        if self.working == 0:
            return []

        self.working -= 1
        endTime = person.get_last_state().service_end_time
        events = []

        if self.queue:
            event = self.putNextEvent(endTime)
            if event:
                events.extend(event)

        compilationSuccess = self.getSuccess()
        if compilationSuccess:
            event = self.end.putInQueue(person, endTime)
        else:
            event = self.instradamento.putInQueue(person, endTime)

        if event:
            events.extend(event)

        return events
