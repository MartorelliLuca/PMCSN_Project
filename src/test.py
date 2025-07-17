from desPython import rvgs
import time

#k=0
#utenti=[]
#for i in range(20000000):
#    if i == 0:
#        start_time = time.time()
#    exp = rvgs.Exponential(1/2)
#    k=k+exp
#    utenti.append(k)
#    if i % 100000 == 0:
#        elapsed = time.time() - start_time
#        progress = (i + 1) / 20000000 * 100
#        print(f"Progress: {progress:.2f}% - Elapsed time: {elapsed:.2f}s", end='\r')
#    if i == 19999999:
#        total_time = time.time() - start_time
#        print(f"\nTotal time: {total_time:.2f}s")
#    

class request:
    def __init__(self, arrival):
        self.path = [["start",arrival,0.0,0.0]]

    def __repr__(self):
        return f"Request(arrival={self.arrival}, service={self.service})"



class simulation:
    def __init__(self):
        pass


class simBlock:

    def __init__(self, name,alpha):
        self.name = name
        self.next = None
        self.queue = []
        self.alpha = alpha  # service rate
        self.working=None

    #da mettere gli handler per gli eventi
    def getNextEvent(self):
        if  len(self.queue) >0 and self.working is None:
            ## restituire il primo elemento della coda senza poppare
            return self.queue[0]
        if self.working is not None:
            return self.working
        
    def addToQueue(self, request):
        self.queue.append(request)
        
    def execute(self, time):
        print(f"Executing {self.name} at time {time}")
        return time + self.delay