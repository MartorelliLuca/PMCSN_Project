# ade_simulation/implementations/fifo_queue.py
from interfaces.Queue import Queue

class FIFOQueue(Queue):
    def __init__(self, distribution_type="deterministic"):
        self.queue = []
        self._distribution = distribution_type

    def distribution(self):
        return self._distribution

    def enqueue(self, item):
        self.queue.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.queue.pop(0)

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)
