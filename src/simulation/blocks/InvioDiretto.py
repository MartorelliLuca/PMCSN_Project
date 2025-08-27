from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta
import math


class InvioDiretto(SimBlockInterface):
    
    def __init__(self, name, mean,variance):
       
        self.name = name
        self.mean = mean
        self.variance = variance
        self.serversNumber=1
        self.queueLenght = 0
        self.queue=[]
        self.working=0
        self.nextBlock = None
        self.lognormal_params = self.calculateParameters()


        
    def setNextBlock(self,nextBlock:SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.nextBlock = nextBlock


    def calculateParameters(self):
        """
        Per una variabile casuale Lognormale(a, b), la media e la varianza sono:

                          media = exp(a + 0.5*b*b)
                       varianza = (exp(b*b) - 1) * exp(2*a + b*b)

        Per rendere la distribuzione il più deterministica possibile, 
        si imposta b molto piccolo (vicino a 0) per minimizzare la varianza.
        """

        # Per una distribuzione quasi deterministica, impostiamo b molto piccolo
        b = 1e-4  # Valore molto piccolo per minimizzare la varianza
        
        # Con b piccolo, a ≈ ln(media)
        a = math.log(self.mean) - 0.5 * (b ** 2)
        
        return [a, b]


    def getServiceTime(self,time:datetime)->datetime:
        a,b=self.lognormal_params
        lognormal = rvgs.Lognormal(a, b)
        return time + timedelta(seconds=lognormal)
    



    
    def get_service_name(self) -> str:
        
        return self.name
    
    def get_serviceRate(self) -> float:
      
        return self.serviceRate    
    
    


    def putInQueue(self,person: Person,timestamp: datetime) ->list[Event]:
        state=NormalState(self.name, timestamp, self.queueLenght)
        self.queueLenght += 1
        self.queue.append(person)
        person.append_state(state)
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
        event=self.nextBlock.putInQueue(serving, endTime)
        
        if event:
            events.extend(event)
        return events


