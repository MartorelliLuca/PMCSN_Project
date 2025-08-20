from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta
import math

from desPython.rvgsCostum import generate_denormalized_bounded_pareto



class InValutazione(SimBlockInterface):
    
    def __init__(self, name, multiServiceRate,mean,variance,accetpanceRate):
       
        self.name = name
        self.mean = mean
        self.variance = variance
        self.multiServiceRate=multiServiceRate
        self.accetpanceRate = accetpanceRate
        self.queueLenght = 0
        self.queue=[]
        self.working=0
        self.instradamento = None
        self.end=None


        
    def setInstradamento(self,instradamento:SimBlockInterface):
        """Imposta il blocco di instradamento."""
        self.instradamento = instradamento

    def setEnd(self,end:SimBlockInterface): 
        """Imposta il blocco di fine."""
        self.end = end

    


    def getServiceTime(self,time:datetime)->datetime:
        lognormal = generate_denormalized_bounded_pareto(1.2,0.01,0.1,1.0,8640,259200)
        return time + timedelta(seconds=lognormal)
    


    def getSuccess(self):
        n=rvgs.Uniform(0,1)
        if n > self.accetpanceRate:
            return False
        return True
    
    def get_service_name(self) -> str:
        
        return self.name
    
    def get_rate(self) -> float:
      
        return self.serviceRate    
    
    


    def putInQueue(self,person: Person,timestamp: datetime) ->list[Event]:
        state=NormalState(self.name, timestamp, self.queueLenght)
        self.queueLenght += 1
        self.queue.append(person)
        person.append_state(state)
        if self.working < self.multiServiceRate:
            events = self.putNextEvenet(timestamp)
            return events if events else []
        return []

    def putNextEvenet(self,exitQueueTime) -> list[Event]:
        if len(self.queue) == 0:
            return []
        if self.working < self.multiServiceRate:
            self.working += 1
            person=self.queue.pop(0)
            if person.get_last_state().enqueue_time > exitQueueTime:
                exitQueueTime = person.get_last_state().enqueue_time
            person.get_last_state().service_start_time = exitQueueTime
            self.queueLenght -= 1
            person.get_last_state().service_end_time = self.getServiceTime(exitQueueTime)
            return [Event(person.get_last_state().service_end_time,  self.name,person, "queue_empty_put_to_work", self.serveNext)]
        return []

    def serveNext(self,person)->list[Event]:
        if self.working == 0:
            return []
        serving=person
        self.working -=1
        endTime = serving.get_last_state().service_end_time
        events=[]
        if self.queue:
            event = self.putNextEvenet(endTime)
            if event:
                events.extend(event)

        compilationSuccess = self.getSuccess()
        if compilationSuccess:
            event=self.end.putInQueue(serving, endTime)
        else:
            event=self.instradamento.putInQueue(serving, endTime)
        if event:
            events.extend(event)
        return events


