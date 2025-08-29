from simulation.states.NormalState import NormalState
from datetime import datetime

class StateWithServiceTime(NormalState):
    def __init__(self, name, enqueue_time, queue_length, serviceTime,queueName):
        super().__init__(name, enqueue_time, queue_length)
        self.serviceTime=serviceTime
        self.queueName=queueName


    def getServiceTime(self) :
        return self.serviceTime

    def get_queue_name(self) :
        return self.queueName   