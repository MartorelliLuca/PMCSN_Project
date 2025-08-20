from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta


class Autenticazione(SimBlockInterface):
    
    def __init__(self, name, serviceRate,multiServiceRate,successProbability,compilazionePrecompilataProbability):
        ''' Remember  to set the following blocks:
        - invioDiretto
        - compilazionePrecompilata
        - instradamento
        '''
        self.name = name
        self.serviceRate = serviceRate
        self.successProbability = successProbability
        self.queueLenght = 0
        self.queue=[]
        self.working=0
        self.compilazionePrecompilata = None
        self.invioDiretto = None
        self.instradamento = None
        self.multiServiceRate = multiServiceRate
        self.compilazionePrecompilataProbability = compilazionePrecompilataProbability

    def setInvioDiretto(self,nextBlock:SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.invioDiretto = nextBlock

    def setCompilazione(self,nextBlock:SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.compilazionePrecompilata = nextBlock

    def setInstradamento(self,instradamento:SimBlockInterface):
        """Imposta il blocco di instradamento."""
        self.instradamento = instradamento

    def getServiceTime(self,time:datetime)->datetime:
      
        exp= rvgs.Exponential(1/self.serviceRate)
        return time + timedelta(seconds=exp)
    

    def isPrecompilata(self):
        """Determina se il modulo è precompilato."""
        n=rvgs.Uniform(0,1)
        if n < self.compilazionePrecompilataProbability:
            return True
        return False
    def get_login_sucess(self):
        n=rvgs.Uniform(0,1)
        if n > self.successProbability:
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

        login_sucess = self.get_login_sucess()
        if not login_sucess:
            event=self.instradamento.putInQueue(serving, endTime)
        else:
            precompilataSuccess= self.isPrecompilata()
            if precompilataSuccess:
                event=self.compilazionePrecompilata.putInQueue(serving, endTime)
            else:
                event=self.invioDiretto.putInQueue(serving, endTime)
        if event:
            events.extend(event)
        return events


