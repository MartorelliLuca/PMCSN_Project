from states.NormalState import NormalState
from datetime import datetime

class StateWithServiceTime(NormalState):
    def __init__(self, name, enqueue_time, queue_length, serviceTime):
        super().__init__(name, enqueue_time, queue_length)
        self.serviceTime=serviceTime

    def getServiceTime(self, current_time: datetime) -> datetime:
        return current_time + self.serviceTime
