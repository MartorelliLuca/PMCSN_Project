from tests.simulation.interface.StateInterface import StateInterface
class NormalState(StateInterface):
    def __init__(self):
        pass

    def queue_length(self) -> int:
        print("Queue length method called")
        pass
    