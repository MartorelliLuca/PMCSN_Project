from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs, rngs


class CompilazionePrecompilataExponential(SimBlockInterface):
    """Blocco multi-server esponenziale per compilazione precompilata."""

    def __init__(self, name, serversNumber, mean, variance, successProbability):
        self.name = name
        self.serversNumber = serversNumber
        self.mean = mean
        self.variance = variance
        self.successProbability = successProbability

        self.queueLenght = 0
        self.queue = []
        self.working = 0
        self.nextBlock = None
        self.stream = 5

    def setNextBlock(self, nextBlock: SimBlockInterface):
        self.nextBlock = nextBlock

    def getServiceTime(self, time: datetime) -> datetime:
        rngs.selectStream(self.stream)
        exp = rvgs.Exponential(self.mean)
        return time + timedelta(seconds=exp)

    def getSuccess(self) -> bool:
        rngs.selectStream(self.stream)
        return rvgs.Uniform(0, 1) <= self.successProbability

    def putInQueue(self, person: Person, timestamp: datetime) -> list[Event]:
        state = NormalState(self.name, timestamp, self.queueLenght)
        self.queueLenght += 1
        self.queue.append(person)
        person.append_state(state)

        if self.working < self.serversNumber:
            events = self.putNextEvent(timestamp)
            return events if events else []
        return []

    def putNextEvent(self, exitQueueTime: datetime) -> list[Event]:
        if not self.queue or self.working >= self.serversNumber:
            return []

        self.working += 1
        person = self.queue.pop(0)
        if person.get_last_state().enqueue_time > exitQueueTime:
            exitQueueTime = person.get_last_state().enqueue_time
        person.get_last_state().service_start_time = exitQueueTime
        self.queueLenght -= 1
        person.get_last_state().service_end_time = self.getServiceTime(exitQueueTime)

        return [Event(
            person.get_last_state().service_end_time,
            self.name,
            person,
            "servizio completato - compilazione precompilata",
            self.serveNext
        )]

    def serveNext(self, person: Person) -> list[Event]:
        if self.working > 0:
            self.working -= 1

        endTime = person.get_last_state().service_end_time
        events = []

        if self.queue:
            new_events = self.putNextEvent(endTime)
            if new_events:
                events.extend(new_events)
        succes=self.getSuccess()
        if succes:
         if self.nextBlock:
            next_events = self.nextBlock.putInQueue(person, endTime)
            if next_events:
                events.extend(next_events)
        else:
            next_events=self.putInQueue(person,endTime)
            if next_events:
                events.extend(next_events)
        return events
