from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta
import json
import os


class EndBlock(SimBlockInterface):
    """Blocco finale della simulazione che registra il completamento delle entità.
    
    Usa streaming writes per ottimizzare performance e memoria.
    """
    def __init__(self, output_file="simulation_results.json"):
        """Inizializza il blocco finale con streaming writes.
        
        Args:
            output_file (str): Nome del file di output (JSON Lines format)
        """
        self.output_file = output_file
        self.total_processed = 0
        self.file_handle = open(self.output_file, 'w', encoding='utf-8', buffering=8192)
        
        # Write metadata as first line
        metadata = {
            "type": "metadata",
            "start_timestamp": datetime.now().isoformat(),
            "format": "json_lines"
        }
        self.file_handle.write(json.dumps(metadata) + '\n')
        self.file_handle.flush()

    def putInQueue(self, person: Person, timestamp: datetime) -> list[Event]:
        """Elabora una persona che completa la simulazione.
        
        Args:
            person: La persona che ha completato la simulazione.
            timestamp: Il timestamp di completamento.
            
        Returns:
            list[Event]: Lista vuota (blocco finale).
        """
        state = NormalState("EndBlock", timestamp, 0)
        person.append_state(state)
        
        # Create JSON representation
        person_data = {
            "type": "entity",
            "person_id": person.ID,
            "completion_timestamp": timestamp.isoformat(),
            "total_states": len(person.states),
            "states": [state.to_dict() for state in person.states],
            "total_simulation_time": (
                (timestamp - person.states[0].enqueue_time).total_seconds()
                if person.states else 0
            )
        }
        
        # Write immediately (streaming)
        self.file_handle.write(json.dumps(person_data) + '\n')
        self.total_processed += 1
        
        # Periodic flush and progress
        if self.total_processed % 1000 == 0:
            self.file_handle.flush()  # Ensure data is written to disk
            #print(f"📊 Processed: {self.total_processed} entities")
            
        return []
    
    def finalize(self):
        """Finalizza la simulazione."""
        # Write final metadata
        final_metadata = {
            "type": "completion",
            "completion_timestamp": datetime.now().isoformat(),
            "total_entities_processed": self.total_processed,
            "simulation_complete": True
        }
        self.file_handle.write(json.dumps(final_metadata) + '\n')
        self.file_handle.close()
        
        print(f"✅ Simulation finalized: {self.total_processed} entities processed")
        print(f"📁 Results saved to: {self.output_file}")
    
    def get_stats(self) -> dict:
        """Restituisce statistiche sulla simulazione corrente."""
        return {
            "total_processed": self.total_processed,
            "output_file": self.output_file,
            "file_open": not self.file_handle.closed
        }