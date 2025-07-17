import heapq
import random
from datetime import datetime, timedelta
from models.person import Person
from models.request import Request
from desPython.rng import putSeed
from desPython import rvgs


class Event:
    def __init__(self, timestamp, event_type, person):
        self.timestamp = timestamp
        self.event_type = event_type  # 'ARRIVAL', 'SERVICE_START', 'SERVICE_END'
        self.person = person

    def __lt__(self, other):
        return self.timestamp < other.timestamp


class EventQueue:
    def __init__(self):
        self.events = []

    def push(self, event):
        heapq.heappush(self.events, event)

    def pop(self):
        return heapq.heappop(self.events)

    def is_empty(self):
        return len(self.events) == 0


class SimulationEngine:
    def __init__(self, service_rate):
        self.event_queue = EventQueue()
        self.queue = []  # waiting queue FIFO
        self.service_rate = service_rate
        self.current_time = 0.0
        self.server_busy = False
        self.serving_person = None

        self.t1_log = []  # [(personID, time_entered_queue)]
        self.t2_log = []  # [(personID, time_started_service)]

        putSeed(123456789)

    def exponential_service_time(self):
        return rvgs.Exponential(1 / self.service_rate)

    def schedule_event(self, timestamp, event_type, person):
        event = Event(timestamp, event_type, person)
        self.event_queue.push(event)

    def initialize(self, person_arrivals):
        for person, arrival_time in person_arrivals:
            self.schedule_event(arrival_time, 'ARRIVAL', person)

    def run(self):
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            self.current_time = event.timestamp
            person = event.person

            if event.event_type == 'ARRIVAL':
                print(f"[{self.current_time:.3f}] Person {person.ID} ARRIVED (executed at {datetime.now()})")
                self.queue.append(person)
                self.t1_log.append((person.ID, self.current_time))

                if not self.server_busy:
                    self.schedule_event(self.current_time, 'SERVICE_START', person)

            elif event.event_type == 'SERVICE_START':
                if self.queue and not self.server_busy:
                    self.server_busy = True
                    person_to_serve = self.queue.pop(0)
                    self.serving_person = person_to_serve
                    service_time = self.exponential_service_time()
                    end_time = self.current_time + service_time
                    self.t2_log.append((person_to_serve.ID, self.current_time))

                    print(f"[{self.current_time:.3f}] Person {person_to_serve.ID} STARTS service (executed at {datetime.now()}), ends at {end_time:.3f}")
                    self.schedule_event(end_time, 'SERVICE_END', person_to_serve)

            elif event.event_type == 'SERVICE_END':
                print(f"[{self.current_time:.3f}] Person {person.ID} ENDS service (executed at {datetime.now()})")
                person.setDestrTime(datetime.now())
                self.server_busy = False
                self.serving_person = None

                # Reschedule ARRIVAL of same person after a pause (simulate requeue)
                delay = 0.5
                next_arrival_time = self.current_time + delay
                self.schedule_event(next_arrival_time, 'ARRIVAL', person)

                if self.queue:
                    next_person = self.queue[0]
                    self.schedule_event(self.current_time, 'SERVICE_START', next_person)

    def print_logs(self):
        print("\nT1: Times people entered the queue")
        for pid, t in self.t1_log:
            print(f"Person {pid} entered queue at {t:.3f}")

        print("\nT2: Times people started service")
        for pid, t in self.t2_log:
            print(f"Person {pid} started service at {t:.3f}")


def Main():
    # Simulazione con 3 persone
    print("Starting Event-Driven Queue Simulation\n")
    service_rate = 0.25  # mean service time = 4.0
    sim = SimulationEngine(service_rate)

    # Setup iniziale persone
    creation_time = datetime.now()
    people = [
        (Person(1, "entry1", creation_time), 0.1),
        (Person(2, "entry2", creation_time), 1.2),
        (Person(3, "entry3", creation_time), 2.8),
    ]

    sim.initialize(people)
    sim.run()
    sim.print_logs()


if __name__ == "__main__":
    Main()