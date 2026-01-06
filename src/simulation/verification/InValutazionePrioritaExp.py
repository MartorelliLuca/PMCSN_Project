from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.StateWithServiceTIme import StateWithServiceTime
from desPython import rvgs, rngs


class InValutazioneCodaPrioritaNP_Exp(SimBlockInterface):
    """
    Versione con TEMPI DI SERVIZIO ESPONENZIALI
    Compatibile con verifica teorica M/M/c con priorità
    """

    def __init__(
        self,
        name,
        mean,
        serversNumber,
        variance,
        successProbability
     ):
        self.stream = 5
        self.name = name

        # Parametri teorici
        self.mean = mean                  # E[S]
        self.mu = 1 / mean                # μ = rate di servizio

        self.serversNumber = serversNumber
        self.variance = variance 

        self.acceptanceRate = successProbability

        # Code di priorità
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
        self.end = None

    # ------------------------------------------------------------------
    # Collegamenti ai blocchi successivi
    # ------------------------------------------------------------------

    def setInvioDiretto(self, nextBlock: SimBlockInterface):
        self.invioDiretto = nextBlock

    def setCompilazione(self, nextBlock: SimBlockInterface):
        self.compilazionePrecompilata = nextBlock

    def setEnd(self, end: SimBlockInterface):
        self.end = end

    # ------------------------------------------------------------------
    # TEMPO DI SERVIZIO ESPONENZIALE
    # ------------------------------------------------------------------

    def getServiceTime(self) -> timedelta:
        rngs.selectStream(self.stream)
        service_time = rvgs.Exponential(self.mean)
        return timedelta(seconds=service_time)

    # ------------------------------------------------------------------
    # Probabilità di esito
    # ------------------------------------------------------------------

    def getSuccess(self) -> bool:
        rngs.selectStream(self.stream + 101)
        return rvgs.Uniform(0, 1) < self.acceptanceRate

    # ------------------------------------------------------------------
    # Metadati servizio
    # ------------------------------------------------------------------

    def get_service_name(self) -> str:
        return self.name

    def get_serviceRate(self) -> float:
        return self.mu

    # ------------------------------------------------------------------
    # Gestione code
    # ------------------------------------------------------------------

    def putInQueue(self, person: Person, timestamp: datetime) -> list[Event]:
        comingFrom = person.get_last_state().get_service_name()
        execTime = self.getServiceTime()

        if comingFrom == "InvioDiretto":
            queueName = "Diretta"
        else:
            if execTime.total_seconds() > self.mean * 1.5:
                queueName = "Pesante"
            else:
                queueName = "Leggera"

        queueLength = self.queueLenght[queueName]
        self.queueLenght[queueName] += 1

        state = StateWithServiceTime(
            self.name,
            timestamp,
            queueLength,
            execTime,
            queueName
        )

        self.queue[queueName].append(person)
        person.append_state(state)

        if self.working < self.serversNumber:
            return self.putNextEvent(timestamp) or []

        return []

    def putNextEvent(self, exitQueueTime: datetime) -> list[Event]:

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
            self.queueLenght[queueName] -= 1

            person.get_last_state().service_start_time = exitQueueTime
            person.get_last_state().service_end_time = exitQueueTime + serviceTime

            return [
                Event(
                    person.get_last_state().service_end_time,
                    self.name,
                    person,
                    "queue_empty_put_to_work",
                    self.serveNext
                )
            ]

        return []

    # ------------------------------------------------------------------
    # Fine servizio
    # ------------------------------------------------------------------

    def serveNext(self, person: Person) -> list[Event]:
        if self.working == 0:
            return []

        self.working -= 1
        endTime = person.get_last_state().service_end_time
        events = []

        next_event = self.putNextEvent(endTime)
        if next_event:
            events.extend(next_event)

        if self.getSuccess():
            event = self.end.putInQueue(person, endTime)
        else:
           event = self.invioDiretto.putInQueue(person, endTime)

        if event:
            events.extend(event)

        return events
