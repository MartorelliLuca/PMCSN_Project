import models.person
from datetime import datetime
from desPython import rvgs 
from desPython.rng import putSeed 


class queue:
    def __init__(self, serviceRate):
        self.serviceRate = serviceRate
        self.coda = []
        self.startingTime = datetime.now()                # person array
        self.currentTick = 0                              # a tick is the minimum udt in the simulation
        self.intraTick = 0                                # 
        self.serving = None                               # person instance
        self.whenServingFinished = 0
        
        # Set random seed for reproducible results
        putSeed(123456789)
    
    def setNextTick(self):
        self.currentTick += 1
        self.intraTick =self.currentTick

    def simulateTick(self):
        self.intraTick = self.currentTick
        
        # Process events that should happen during this tick
        events_processed = True
        while events_processed:
            events_processed = False
            
            # Check if we can start serving someone
            if self.serving is None and len(self.coda) > 0:
                # Get the next person in queue
                self.serving = self.coda.pop(0)
                # Service starts at max of current time and person's arrival time
                self.intraTick = max(self.intraTick, self.serving[1])
                # Generate service time (mean = 1/serviceRate, so use serviceRate as mean parameter)
                exp=rvgs.Exponential(1/self.serviceRate)
                service_time = exp
                self.whenServingFinished = self.intraTick + service_time
                print(f"Person {self.serving[0].ID} started being served at tick {self.intraTick:.3f}, exp {exp},will finish at {self.whenServingFinished:.3f}")
                events_processed = True
            
            # Check if current service finishes within this tick
            if self.serving is not None and self.whenServingFinished <= self.currentTick + 1:
                self.intraTick = self.whenServingFinished
                print(f"Person {self.serving[0].ID} finished being served at tick {self.intraTick:.3f}")
                self.serving[0].setDestrTime(datetime.now())
                self.serving = None
                events_processed = True
        
        self.currentTick += 1
            

        
    
    def putInQueue(self, person, tickArrival):
        self.coda.append([person, tickArrival])
        # Sort by arrival time to maintain FIFO order for simultaneous arrivals
        self.coda.sort(key=lambda x: x[1])
        print(f"Person {person.ID} entered the queue at arrival tick {tickArrival} (current tick: {self.currentTick})")

        

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