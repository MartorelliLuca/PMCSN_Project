from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta
import math


class InEsame(SimBlockInterface):
    
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
        self.lognormal_params = self.calculateParameters()


        
    def setInstradamento(self,instradamento:SimBlockInterface):
        """Imposta il blocco di instradamento."""
        self.instradamento = instradamento

    def setEnd(self,end:SimBlockInterface): 
        """Imposta il blocco di fine."""
        self.end = end

    def calculateParameters(self):
        """
        Per una variabile casuale Lognormale(a, b), la media e la varianza sono:

                          media = exp(a + 0.5*b*b)
                       varianza = (exp(b*b) - 1) * exp(2*a + b*b)

        I parametri a e b devono essere scelti in accordo con la media e varianza desiderate
        """
    
        # Calcolo dei parametri a e b dalla media e varianza
        # b^2 = ln(1 + varianza/media^2)
        b_squared = math.log(1 + self.variance / (self.mean ** 2))
        b = math.sqrt(b_squared)
        
        # a = ln(media) - 0.5*b^2
        a = math.log(self.mean) - 0.5 * b_squared
        return [a,b]


    def getServiceTime(self,time:datetime)->datetime:
        a,b=self.lognormal_params
        lognormal = rvgs.Lognormal(a, b)
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


