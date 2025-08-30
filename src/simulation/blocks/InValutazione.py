from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta
import math

from desPython.rvgsCostum import generate_denormalized_bounded_pareto,find_best_normalized_pareto_params



class InValutazione(SimBlockInterface):
    
    def __init__(self, name, dipendenti,pratichePerDipendente, mean, variance, successProbability):
       
        self.stream = 5
        self.name = name
        self.mean = mean
        self.variance = variance
        self.serversNumber = dipendenti*pratichePerDipendente
        self.accetpanceRate = successProbability
        self.queueLenght = 0
        self.queue=[]
        self.working=0
        self.instradamento = None
        self.end=None
        self.lower_bound=mean*0.001
        self.upper_bound=mean*8
        self.a,self.k = find_best_normalized_pareto_params(
            original_mean=mean,
            original_l=self.lower_bound,
            original_h=self.upper_bound,
            save_plot=True,
            verbose=True  # Suppress print messages
        )

        
    def setInstradamento(self,instradamento:SimBlockInterface):
        """Imposta il blocco di instradamento."""
        self.instradamento = instradamento

    def setEnd(self,end:SimBlockInterface): 
        """Imposta il blocco di fine."""
        self.end = end

    


    def getServiceTime(self,time:datetime)->datetime:
        from desPython import rngs
        rngs.selectStream(self.stream)
        lognormal = generate_denormalized_bounded_pareto(self.a,self.k,0.1,1.0,self.lower_bound,self.upper_bound)
        return time + timedelta(seconds=lognormal)
    


    def getSuccess(self):
        from desPython import rngs
        rngs.selectStream(self.stream)
        n=rvgs.Uniform(0,1)
        if n > self.accetpanceRate:
            return False
        return True
    
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


