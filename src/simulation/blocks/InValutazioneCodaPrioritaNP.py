from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.StateWithServiceTIme import StateWithServiceTime
from desPython import rvgs
from datetime import timedelta
import math

from desPython.rvgsCostum import generate_denormalized_bounded_pareto,find_best_normalized_pareto_params



class InValutazioneCodaPrioritaNP(SimBlockInterface):
    
    def __init__(self, name, dipendenti,pratichePerDipendente, mean, variance, successProbability, dropoutProbability, precompilataProbability):
       
        self.stream = 5
        self.name = name
        self.mean = mean
        self.variance = variance
        self.serversNumber = dipendenti*pratichePerDipendente
        self.normalServerNumber=self.serversNumber
        self.acceptanceRate = successProbability
        self.dropoutProbability = dropoutProbability
        self.precompilataProbability = precompilataProbability
        self.queueLenght = {
            "Diretta":0,
            "Pesante":0,
            "Leggera":0
        }
        self.queue=  {
            "Diretta":[],
            "Pesante":[],
            "Leggera":[]
        }

        self.working=0
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

        
    def setInvioDiretto(self,nextBlock:SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.invioDiretto = nextBlock

    def setCompilazione(self,nextBlock:SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.compilazionePrecompilata = nextBlock

    def setEnd(self,end:SimBlockInterface): 
        """Imposta il blocco di fine."""
        self.end = end

    

    def getServiceTime(self)->datetime:
        from desPython import rngs
        rngs.selectStream(self.stream)
        lognormal = generate_denormalized_bounded_pareto(self.a,self.k,0.1,1.0,self.lower_bound,self.upper_bound)
        return timedelta(seconds=lognormal)

    def getDropout(self):
        from desPython import rngs
        rngs.selectStream(self.stream+100)
        n=rvgs.Uniform(0,1)
        if n > self.dropoutProbability:
            return False
        return True


    def getServiceTimeOld(self,time:datetime)->datetime:
        from desPython import rngs
        rngs.selectStream(self.stream)
        lognormal = generate_denormalized_bounded_pareto(self.a,self.k,0.1,1.0,self.lower_bound,self.upper_bound)
        return timedelta(seconds=lognormal)
    


    def getSuccess(self):
        from desPython import rngs
        rngs.selectStream(self.stream+100)
        n=rvgs.Uniform(0,1)
        if n > self.acceptanceRate:
            return False
        return True
    
    def get_service_name(self) -> str:
        
        return self.name
    
    def get_serviceRate(self) -> float:
      
        return self.serviceRate    

    def isPrecompilata(self):
        """Determina se il modulo è precompilato."""
        from desPython import rngs
        rngs.selectStream(self.stream)
        n=rvgs.Uniform(0,1)
        if n < self.precompilataProbability:
            return True
        return False

    def putInQueue(self,person: Person,timestamp: datetime) ->list[Event]:
        comingFrom=person.get_last_state().get_service_name()
        execTime=self.getServiceTime()
        queueLength=0
        queueName=""    
        if comingFrom=="InvioDiretto":
                queueName="Diretta"            
        else:
            if execTime.total_seconds()>(self.mean*1.5):
                queueName="Pesante"
            else:
                queueName="Leggera"

        queueLength=self.queueLenght[queueName]
        self.queueLenght[queueName] += 1
        
        state=StateWithServiceTime(self.name, timestamp, queueLength,execTime,queueName)
        
        self.queue[queueName].append(person)    
        
        person.append_state(state)
        
        if self.working < self.serversNumber:
            events = self.putNextEvent(timestamp)
            return events if events else []
        return []

    def putNextEvent(self,exitQueueTime) -> list[Event]:

        queueName=""
        if self.queueLenght["Diretta"]>0:
            queueName="Diretta"
        else:
            if self.queueLenght["Leggera"]>0:
                queueName="Leggera"
            else:
                if self.queueLenght["Pesante"]>0:
                    queueName="Pesante"
                else:
                    return []
        if self.working < self.serversNumber:
            self.working += 1
            person=self.queue[queueName].pop(0)
            serviceTime=person.get_last_state().getServiceTime()
            person.get_last_state().service_start_time = exitQueueTime
            self.queueLenght[queueName] -= 1

            person.get_last_state().service_end_time = exitQueueTime + serviceTime
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
            event = self.putNextEvent(endTime)
            if event:
                events.extend(event)

        compilationSuccess = self.getSuccess()
        if compilationSuccess:
            event=self.end.putInQueue(serving, endTime)
        else:
            compilationDropout = self.getDropout()
            if compilationDropout:
                #butta fuori dal sistema
                event=self.end.putInQueue(serving, endTime)
            else:        
                precompilataSuccess= self.isPrecompilata()
                if precompilataSuccess:
                    event=self.compilazionePrecompilata.putInQueue(serving, endTime)
                else:
                    event=self.invioDiretto.putInQueue(serving, endTime)
        if event:
            events.extend(event)
        return events


