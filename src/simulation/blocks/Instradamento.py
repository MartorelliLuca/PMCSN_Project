from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta


class Instradamento(SimBlockInterface):
    
    def __init__(self, name, serviceRate,serversNumber,queueMaxLenght):
        
        self.endBlock = None
       
        self.queueMaxLenght = queueMaxLenght
        self.name = name
        self.serviceRate = serviceRate
        self.queueLenght = 0
        self.queue=[]
        self.working=0
        self.nextBlock = None
        self.serversNumber = serversNumber

    def setQueueFullFallBackBlock(self,endBlock:SimBlockInterface):
        """Imposta il blocco finale da chiamare quando la coda è piena."""
        self.endBlock = endBlock

    def setNextBlock(self,nextBlock:SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.nextBlock = nextBlock

    def getServiceTime(self,time:datetime)->datetime:
      
        exp= rvgs.Exponential(1/self.serviceRate)
        return time + timedelta(seconds=exp)
    

    def get_service_name(self) -> str:
        
        return self.name
    
    def get_serviceRate(self) -> float:
      
        return self.serviceRate    
    
    def putInQueue(self,person: Person,timestamp: datetime) ->list[Event]:

        state=NormalState(self.name, timestamp, self.queueLenght)
        self.queue.append(person)
        person.append_state(state)
        if self.queueLenght >= self.queueMaxLenght:
            #TODO fare in modo che il blocco finale si accorga che il l'utente è stato scartato
            event= self.endBlock.putInQueue(person, timestamp)
            return event if event else []
        self.queueLenght += 1
        if self.working < self.serversNumber:
            events = self.putNextEvenet(timestamp)
            return events if events else []
        return []

    def putNextEvenet(self,exitQueueTime) -> list[Event]:

        if len(self.queue) == 0:
            return []
        if self.working < self.serversNumber:
            self.working += 1
            person=self.queue.pop(0)
           
            if person.get_last_state().enqueue_time > exitQueueTime:
                exitQueueTime = person.get_last_state().enqueue_time
            person.get_last_state().service_start_time = exitQueueTime
            self.queueLenght -= 1
            person.get_last_state().service_end_time = self.getServiceTime(exitQueueTime)
            return [Event(person.get_last_state().service_end_time,  self.name,person, f"{self.working-1} pepole where working", self.serveNext)]
        return []

    def serveNext(self,person)->list[Event]:
        assert self.working >= 0, "Working should not be negative"
        if self.working==0:
            return []
        serving=person
        self.working -=1
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


