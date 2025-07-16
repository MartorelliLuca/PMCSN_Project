from interfaces.LoadBalancer import LoadBalancer

class FIFO_LoadBalancer(LoadBalancer):
    def assign_priority(self, request: dict) -> int:
        return 1  # tutti uguali in questa implementazione dummy