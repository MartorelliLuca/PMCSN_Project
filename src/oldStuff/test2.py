import models.person
from datetime import datetime
from desPython import rvgs 
from desPython.rng import putSeed 

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


class queue:
    def __init__(self, serviceRate):
        self.serviceRate = serviceRate
        self.coda = []
        self.startingTime = datetime.now()                # person array
        self.serving = None                               # person instance
        self.whenServingFinished = 0
        
        # Set random seed for reproducible results
        putSeed(1)
    
    

class request:
    def __init__(self, arrival):
        self.path = [["start",arrival,0.0]]

    def __repr__(self):
        return f"Request(arrival={self.arrival}, service={self.service})"


class simBlock:
    def __init__(self, name,alpha):
        self.name = name
        self.next = None
        self.queue = []
        self.alpha = alpha  # service rate

    def setNext(self, next_block):
        self.next = next_block

    def addToQueue(self, request):
        self.queue.append(request)
        
    def execute(self, time):
        print(f"Executing {self.name} at time {time}")
        return time + self.delay



def Main():
    # Service rate of 0.25 means average service time = 1/0.25 = 4 time units
    print("Starting Queue Simulation")
    print("Service rate: 0.25 (mean service time: 4.0 time units)")
    print("=" * 50)
    
    sim = queue(0.25)
    
    # Add people to queue with their arrival times
    sim.putInQueue(models.person.Person(1, "entry1", datetime.now()), 0.0)
    sim.putInQueue(models.person.Person(2, "entry2", datetime.now()), 0.1)
    sim.putInQueue(models.person.Person(3, "entry3", datetime.now()), 0.2)
    sim.putInQueue(models.person.Person(4, "entry4", datetime.now()), 0.1)  # This will be sorted after person 2
    sim.putInQueue(models.person.Person(5, "entry5", datetime.now()), 0.3)
    sim.putInQueue(models.person.Person(6, "entry6", datetime.now()), 0.7)
    
    print("\nStarting simulation...")
    print("=" * 50)
    
    # Run simulation for enough ticks to process all customers
    for tick in range(16):
        print(f"\n--- Processing Tick {tick} ---")
        sim.simulateTick()
        
        # Show current queue status
        if len(sim.coda) > 0:
            waiting_ids = [person[0].ID for person in sim.coda]
            print(f"People waiting in queue: {waiting_ids}")
        else:
            print("Queue is empty")
            
        if sim.serving is not None:
            print(f"Currently serving: Person {sim.serving[0].ID}")
        else:
            print("Server is idle")
            
        print("-" * 30)


if __name__ == "__main__":
    Main()