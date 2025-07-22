from interfaces.StateInterface import StateInterface
from datetime import datetime

class NormalState(StateInterface):
    def __init__(self,name,enqueue_time,queue_length):
        self.name = name
        self.enqueue_time = enqueue_time
        self.queue_length = queue_length
        self.service_start_time = None
        self.service_end_time = None

    def get_service_name(self) -> str:
        return self.name
    
    def get_queue_enter_time(self) -> datetime:
        return self.enqueue_time
    
    def get_queue_exit_time(self) -> datetime:
        return self.service_end_time if self.service_end_time else None
    
    def get_working_end(self) -> datetime:
        return self.service_end_time if self.service_end_time else None


    def queue_length(self) -> int:
        return self.queue_length

    def get_next_event_time(self) -> datetime:
        return self.service_end_time if self.service_end_time else self.enqueue_time

    def to_dict(self) -> dict:
        """Converte lo stato in un dizionario per la serializzazione JSON."""
        return {
            "service_name": self.name,
            "enqueue_time": self.enqueue_time.isoformat() if self.enqueue_time else None,
            "service_start_time": self.service_start_time.isoformat() if self.service_start_time else None,
            "service_end_time": self.service_end_time.isoformat() if self.service_end_time else None,
            "queue_length": self.queue_length,
            "service_duration_seconds": (
                (self.service_end_time - self.service_start_time).total_seconds() 
                if self.service_start_time and self.service_end_time 
                else None
            )
        }