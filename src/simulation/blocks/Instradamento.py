from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta


class Instradamento(SimBlockInterface):
    
    def __init__(self, name, rate, nextBlock:SimBlockInterface):
       
        self.name = name
        self.rate = rate
        self.queueLenght = 0
        self.queue=[]
        self.working=None
        self.nextBlock = nextBlock

    def getServiceTime(self,time:datetime)->datetime:
      
        exp= rvgs.Exponential(1/self.rate)
        return time + timedelta(seconds=exp)
    

    def get_service_name(self) -> str:
        
        return self.name
    
    def get_rate(self) -> float:
      
        return self.rate    
    
    def putInQueue(self,person: Person,timestamp: datetime) ->list[Event]:

        state=NormalState(self.name, timestamp, self.queueLenght)
        self.queueLenght += 1
        self.queue.append(person)
        person.append_state(state)
        if self.working is None:
            events = self.putNextEvenet(timestamp)
            return events if events else []
        return []

    def putNextEvenet(self,exitQueueTime) -> list[Event]:

        if len(self.queue) == 0:
            return []
        if self.working is None:
            self.working=self.queue.pop(0)
            if self.working.get_last_state().enqueue_time > exitQueueTime:
                exitQueueTime = self.working.get_last_state().enqueue_time
            self.working.get_last_state().service_start_time = exitQueueTime
            self.queueLenght -= 1
            self.working.get_last_state().service_end_time = self.getServiceTime(exitQueueTime)
            return [Event(self.working.get_last_state().service_end_time,  self.name,self.working, "queue_empty_put_to_work", self.serveNext)]
        return []

    def serveNext(self)->list[Event]:
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


