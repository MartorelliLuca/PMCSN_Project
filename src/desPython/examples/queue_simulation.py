#!/usr/bin/env python3
"""
Queue Simulation with Exponential Arrivals and Service Times
Using the desPython library for random variate generation
"""

import sys
sys.path.append('desPython')  # Add the desPython directory to path

from desPython.rvgs import Exponential
from desPython.rng import putSeed
import heapq
from collections import deque

class Event:
    """Event class for discrete event simulation"""
    def __init__(self, time, event_type, customer_id=None):
        self.time = time
        self.event_type = event_type  # 'arrival' or 'departure'
        self.customer_id = customer_id
    
    def __lt__(self, other):
        return self.time < other.time

class QueueSimulation:
    """M/M/1 Queue Simulation (Exponential arrivals, Exponential service, 1 server)"""
    
    def __init__(self, arrival_rate, service_rate, seed=123456789):
        """
        Initialize the queue simulation
        
        Args:
            arrival_rate: Lambda (average arrivals per time unit)
            service_rate: Mu (average service completions per time unit)
            seed: Random number generator seed
        """
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.mean_interarrival_time = 1.0 / arrival_rate
        self.mean_service_time = 1.0 / service_rate
        
        # Initialize random number generator
        putSeed(seed)
        
        # Simulation state
        self.current_time = 0.0
        self.event_list = []  # Priority queue of events
        self.queue = deque()  # Customer queue
        self.server_busy = False
        self.next_customer_id = 1
        
        # Statistics
        self.total_customers = 0
        self.customers_served = 0
        self.total_wait_time = 0.0
        self.total_system_time = 0.0
        self.max_queue_length = 0
        self.area_under_queue_length = 0.0
        self.last_event_time = 0.0
        
        # Customer tracking
        self.customer_arrival_times = {}
        self.customer_service_start_times = {}
    
    def schedule_event(self, event):
        """Add an event to the event list"""
        heapq.heappush(self.event_list, event)
    
    def generate_next_arrival(self):
        """Generate the next arrival event"""
        interarrival_time = Exponential(self.mean_interarrival_time)
        arrival_time = self.current_time + interarrival_time
        arrival_event = Event(arrival_time, 'arrival', self.next_customer_id)
        self.schedule_event(arrival_event)
        self.next_customer_id += 1
    
    def process_arrival(self, customer_id):
        """Process a customer arrival"""
        self.total_customers += 1
        self.customer_arrival_times[customer_id] = self.current_time
        
        if not self.server_busy:
            # Server is free, start service immediately
            self.start_service(customer_id)
        else:
            # Server is busy, add customer to queue
            self.queue.append(customer_id)
            self.max_queue_length = max(self.max_queue_length, len(self.queue))
    
    def start_service(self, customer_id):
        """Start service for a customer"""
        self.server_busy = True
        self.customer_service_start_times[customer_id] = self.current_time
        
        # Calculate wait time (time from arrival to start of service)
        wait_time = self.current_time - self.customer_arrival_times[customer_id]
        self.total_wait_time += wait_time
        
        # Schedule departure event
        service_time = Exponential(self.mean_service_time)
        departure_time = self.current_time + service_time
        departure_event = Event(departure_time, 'departure', customer_id)
        self.schedule_event(departure_event)
    
    def process_departure(self, customer_id):
        """Process a customer departure"""
        self.customers_served += 1
        
        # Calculate total time in system
        system_time = self.current_time - self.customer_arrival_times[customer_id]
        self.total_system_time += system_time
        
        # Clean up customer data
        del self.customer_arrival_times[customer_id]
        del self.customer_service_start_times[customer_id]
        
        if self.queue:
            # Start service for next customer in queue
            next_customer = self.queue.popleft()
            self.start_service(next_customer)
        else:
            # No customers waiting, server becomes idle
            self.server_busy = False
    
    def update_statistics(self):
        """Update time-weighted statistics"""
        time_increment = self.current_time - self.last_event_time
        self.area_under_queue_length += len(self.queue) * time_increment
        self.last_event_time = self.current_time
    
    def run_simulation(self, simulation_time):
        """Run the simulation for the specified time"""
        # Schedule first arrival
        self.generate_next_arrival()
        
        while self.event_list and self.current_time < simulation_time:
            # Get next event
            event = heapq.heappop(self.event_list)
            
            # Update statistics before processing event
            self.update_statistics()
            
            # Update simulation time
            self.current_time = event.time
            
            if event.event_type == 'arrival':
                self.process_arrival(event.customer_id)
                # Schedule next arrival (only if within simulation time)
                if self.current_time < simulation_time:
                    self.generate_next_arrival()
            
            elif event.event_type == 'departure':
                self.process_departure(event.customer_id)
        
        # Final statistics update
        self.current_time = simulation_time
        self.update_statistics()
    
    def print_results(self):
        """Print simulation results and statistics"""
        print("=" * 60)
        print("QUEUE SIMULATION RESULTS")
        print("=" * 60)
        print(f"Simulation Parameters:")
        print(f"  Arrival rate (λ): {self.arrival_rate:.2f} customers/time unit")
        print(f"  Service rate (μ): {self.service_rate:.2f} customers/time unit")
        print(f"  Traffic intensity (ρ = λ/μ): {self.arrival_rate/self.service_rate:.3f}")
        print(f"  Mean interarrival time: {self.mean_interarrival_time:.3f}")
        print(f"  Mean service time: {self.mean_service_time:.3f}")
        print()
        
        print(f"Simulation Results:")
        print(f"  Total customers arrived: {self.total_customers}")
        print(f"  Total customers served: {self.customers_served}")
        print(f"  Customers still in system: {self.total_customers - self.customers_served}")
        print(f"  Maximum queue length: {self.max_queue_length}")
        print()
        
        if self.customers_served > 0:
            avg_wait_time = self.total_wait_time / self.customers_served
            avg_system_time = self.total_system_time / self.customers_served
            avg_queue_length = self.area_under_queue_length / self.current_time
            
            print(f"Performance Metrics:")
            print(f"  Average wait time in queue: {avg_wait_time:.4f}")
            print(f"  Average time in system: {avg_system_time:.4f}")
            print(f"  Average queue length: {avg_queue_length:.4f}")
            print(f"  Server utilization: {(self.current_time - self.area_under_queue_length / len(self.queue) if self.queue else self.current_time) / self.current_time:.4f}")
        
        print()
        print("Theoretical Results (M/M/1 queue):")
        rho = self.arrival_rate / self.service_rate
        if rho < 1.0:
            theoretical_avg_customers = rho / (1 - rho)
            theoretical_avg_wait = rho / (self.service_rate * (1 - rho))
            theoretical_avg_system = 1 / (self.service_rate * (1 - rho))
            
            print(f"  Traffic intensity (ρ): {rho:.3f}")
            print(f"  Average number in system: {theoretical_avg_customers:.4f}")
            print(f"  Average wait time: {theoretical_avg_wait:.4f}")
            print(f"  Average system time: {theoretical_avg_system:.4f}")
        else:
            print(f"  System is unstable (ρ = {rho:.3f} ≥ 1)")

def main():
    """Example usage of the queue simulation"""
    print("Queue Simulation with Exponential Arrivals and Service Times")
    print("Using desPython library for random number generation")
    print()
    
    # Simulation parameters
    arrival_rate = 0.8    # customers per time unit
    service_rate = 1.0    # customers per time unit  
    simulation_time = 1000.0
    
    # Create and run simulation
    sim = QueueSimulation(arrival_rate, service_rate)
    sim.run_simulation(simulation_time)
    sim.print_results()

if __name__ == "__main__":
    main()
