from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs
from datetime import timedelta
import json


class EndBlock(SimBlockInterface):
    """Blocco finale della simulazione che registra il completamento delle entità.
    
    Gestisce la raccolta e formattazione dei risultati della simulazione sia in formato
    testuale che JSON per l'analisi dei dati.
    """
    def __init__(self):
        """Inizializza il blocco finale con array per log testuale e JSON."""
        self.output_log = []
        self.json_log = []

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
            "person_id": person.ID,
            "completion_timestamp": timestamp.isoformat(),
            "total_states": len(person.states),
            "states": [state.to_dict() for state in person.states],
            "total_simulation_time": (
                (timestamp - person.states[0].enqueue_time).total_seconds()
                if person.states else 0
            )
        }
        self.json_log.append(person_data)
        
        # Collect text output
        output = []
        output.append("\n" + "="*50)
        output.append(f"🏁 END BLOCK - Person {person.ID} has completed the simulation")
        output.append(f"   Final timestamp: {timestamp}")
        output.append("="*50)
        
        # Display the state chain
        output.append(f"\n📊 State Chain for Person {person.ID}:")
        output.append("   " + "-" * 40)
        
        for i, state in enumerate(person.states):
            service_duration = "N/A"
            if hasattr(state, 'service_start_time') and hasattr(state, 'service_end_time'):
                if state.service_start_time and state.service_end_time:
                    duration = state.service_end_time - state.service_start_time
                    service_duration = f"{duration.total_seconds():.2f}s"
            
            output.append(f"   [{i+1}] Service: {state.name}")
            output.append(f"       Queue Entry: {state.enqueue_time}")
            if hasattr(state, 'service_start_time') and state.service_start_time:
                output.append(f"       Service Start: {state.service_start_time}")
            if hasattr(state, 'service_end_time') and state.service_end_time:
                output.append(f"       Service End: {state.service_end_time}")
            output.append(f"       Service Duration: {service_duration}")
            if i < len(person.states) - 1:
                output.append("       ↓")
        
        output.append("   " + "-" * 40)
        output.append("✅ Person processing complete!\n")
        
        # Add to the main log and print both formats
        self.output_log.extend(output)
        
        # Print text format
        #for line in output:
            #print(line)
            
        # Print JSON format
        #print(f"\n📊 JSON Data for Person {person.ID}:")
        #print(json.dumps(person_data, indent=2, ensure_ascii=False))
        #print("-" * 50)
            
        return []
    
    def write_output_to_file(self, filename="simulation_results.txt"):
        """Scrive tutto l'output raccolto in un file di testo.
        
        Args:
            filename (str): Nome del file di output. Default: "simulation_results.txt"
        """
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                for line in self.output_log:
                    file.write(line + '\n')
            print(f"📁 Risultati testuali scritti in: {filename}")
        except Exception as e:
            print(f"❌ Errore nella scrittura del file {filename}: {e}")
    
    def write_json_to_file(self, filename="simulation_results.json"):
        """Scrive tutti i dati JSON in un file.
        
        Args:
            filename (str): Nome del file JSON. Default: "simulation_results.json"
        """
        try:
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump({
                    "simulation_results": self.json_log,
                    "total_persons": len(self.json_log),
                    "export_timestamp": datetime.now().isoformat()
                }, file, indent=2, ensure_ascii=False)
            print(f"📊 Dati JSON scritti in: {filename}")
        except Exception as e:
            print(f"❌ Errore nella scrittura del file JSON {filename}: {e}")
    
    def write_all_outputs(self, text_filename="simulation_results.txt", 
                          json_filename="simulation_results.json"):
        """Scrive sia l'output testuale che i dati JSON.
        
        Args:
            text_filename (str): Nome del file di testo.
            json_filename (str): Nome del file JSON.
        """
        self.write_output_to_file(text_filename)
        self.write_json_to_file(json_filename)
    
    def clear_output_log(self):
        """Svuota sia i log testuali che JSON."""
        self.output_log = []
        self.json_log = []
        print("🗑️ Log di output svuotati")
    
    def get_json_data(self) -> list:
        """Restituisce i dati JSON raccolti.
        
        Returns:
            list: Lista dei dati JSON delle persone processate.
        """
        return self.json_log 