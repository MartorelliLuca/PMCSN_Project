from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs, rngs


class CompilazionePrecompilataExponential(SimBlockInterface):

    def __init__(self, name, serversNumber, mean, variance, successProbability):
        self.stream = 3
        self.name = name
        self.mean = mean
        self.serversNumber = serversNumber
        self.compilationSuccessRate = successProbability

        self.queueLenght = 0
        self.queue = []
        self.working = 0
        self.nextBlock = None

    # ----------------------------
    # Routing
    # ----------------------------
    def setNextBlock(self, nextBlock: SimBlockInterface):
        self.nextBlock = nextBlock

    # ----------------------------
    # Service time (EXPONENTIAL)
    # ----------------------------
    def getServiceTime(self, time: datetime) -> datetime:
        rngs.selectStream(self.stream)
        service_time = rvgs.Exponential(self.mean)
        return time + timedelta(seconds=service_time)

    # ----------------------------
    # Success probability
    # ----------------------------
    def getSuccess(self):
        rngs.selectStream(self.stream + 100)
        return rvgs.Uniform(0, 1) < self.compilationSuccessRate

    # ----------------------------
    # Queue logic (immutata)
    # ----------------------------
    def putInQueue(self, person: Person, timestamp: datetime):
        state = NormalState(self.name, timestamp, self.queueLenght)
        self.queueLenght += 1
        self.queue.append(person)
        person.append_state(state)

        if self.working < self.serversNumber:
            return self.putNextEvent(timestamp) or []
        return []

    def putNextEvent(self, exitQueueTime):
        if not self.queue or self.working >= self.serversNumber:
            return []

        self.working += 1
        person = self.queue.pop(0)

        if person.get_last_state().enqueue_time > exitQueueTime:
            exitQueueTime = person.get_last_state().enqueue_time

        person.get_last_state().service_start_time = exitQueueTime
        self.queueLenght -= 1

        end_time = self.getServiceTime(exitQueueTime)
        person.get_last_state().service_end_time = end_time

        return [Event(end_time, self.name, person, "service_end", self.serveNext)]

    def serveNext(self, person):
        self.working -= 1
        endTime = person.get_last_state().service_end_time
        events = []

        if self.queue:
            events.extend(self.putNextEvent(endTime))

        if self.getSuccess():
            events.extend(self.nextBlock.putInQueue(person, endTime))
        else:
            events.extend(self.putInQueue(person, endTime))

        return events
