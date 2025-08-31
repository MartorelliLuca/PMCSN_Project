from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
import json

from simulation.blocks.StartBlock import StartBlock


class EndBlock(SimBlockInterface):
    """Blocco finale che raccoglie, aggrega e salva risultati giornalieri della simulazione."""

    def __init__(self, output_file="daily_stats.json"):
        self.output_file = output_file
        self.file_handle = open(self.output_file, 'w', encoding='utf-8', buffering=8192)

        # Scrive intestazione metadata
        metadata = {
            "type": "metadata",
            "start_timestamp": datetime.now().isoformat(),
            "format": "json_lines_per_day"
        }
        self.file_handle.write(json.dumps(metadata) + '\n')
        self.file_handle.flush()

        # Variabili di stato
        self.workingDate = None               # giorno attualmente in elaborazione
        self.daily_stats = {}    
        self.day_summary={
                    "entrati": 0,
                    "usciti": 0,
                    "trovato_coda_piena": 0
                }           # dizionario con stats per giorno
        self.total_processed = 0
        self.start_block= None  # riferimento al blocco di partenza

    def setStartBlock(self, start_block: StartBlock):
        """Imposta il blocco di partenza per la simulazione.
        
        Args:
            start_block (SimBlockInterface): Il blocco di partenza della simulazione.
        """
        self.start_block = start_block


    def get_entrate_nel_sistema(self, date: datetime):
        if self.start_block:
            # Convert date (datetime.date) to datetime (datetime.datetime) at midnight
            date_as_datetime = datetime.combine(date, datetime.min.time())
            return self.start_block.get_entrate_nel_sistema(date_as_datetime)
        return 0
    
    def _flush_day(self):
        """Scrive le statistiche aggregate del giorno corrente su file e resetta la struttura."""
        if self.workingDate is None or not self.daily_stats:
            return
        self.day_summary["entrati"] = self.get_entrate_nel_sistema(self.workingDate)

        for queue, stats in self.daily_stats.items():
            if stats["visited"] > 0:
                stats["queue_time"] /= stats["visited"]
                stats["queue_lenght"] /= stats["visited"]
                stats["executing_time"] /= stats["visited"]
            else:
                stats["queue_time"] = 0
                stats["queue_lenght"] = 0
                stats["executing_time"] = 0
        output = {
            "type": "daily_summary",
            "date": self.workingDate.isoformat(),
            "summary": self.day_summary,
            "stats": self.daily_stats
        }

        self.file_handle.write(json.dumps(output) + '\n')
        self.file_handle.flush()
        self.daily_stats = {}
        self.day_summary={
                    "entrati": 0,
                    "usciti": 0,
                    "trovato_coda_piena": 0
                }

    def _update_stats(self, person: Person):
        """Aggiorna le statistiche del giorno corrente con i dati di una persona."""
        last_state = person.get_last_state()

        
        self.day_summary["usciti"] += 1

        for state in person.states:
            queue = state.name
            if queue == "Start":
                continue
            
            time_in_queue = (state.service_start_time-state.enqueue_time).total_seconds() if state.service_start_time else None
            time_executing = (state.service_end_time-state.service_start_time).total_seconds() if state.service_start_time else None
            in_code= state.queue_length if state.queue_length else 0


            if queue not in self.daily_stats:
                self.daily_stats[queue] = {
                    "visited": 1,
                    "queue_time": time_in_queue,
                    "queue_lenght": in_code,
                    "executing_time": time_executing,
                    "data": {
                            "queue_time": [time_in_queue,],
                            "queue_lenght": [in_code,],
                            "executing_time": [time_executing,],
                    } 
                }
            else:
                stat = self.daily_stats[queue]
                stat["visited"] += 1
                stat["queue_time"] += time_in_queue
                stat["queue_lenght"] += in_code
                stat["executing_time"] += time_executing
                if stat["visited"] < 50*16 and stat["visited"] % 16 == 0:
                    stat["data"]["queue_time"].append(time_in_queue)
                    stat["data"]["queue_lenght"].append(in_code)
                    stat["data"]["executing_time"].append(time_executing)

    def putInQueue(self, person: Person, timestamp: datetime) -> list[Event]:
        """Riceve una persona che ha completato il sistema. Calcola e aggrega i dati giornalieri.
        
        Args:
            person (Person): L'entità completata.
            timestamp (datetime): Quando ha lasciato il sistema.

        Returns:
            list[Event]: Lista vuota (blocco finale).
        """
        completion_date = timestamp.date()

        # Cambiamento giorno? Flush precedente e reset stats
        if self.workingDate is None:
            self.workingDate = completion_date
        elif completion_date != self.workingDate:
            self._flush_day()
            self.workingDate = completion_date

        # Salva stato finale
        #state = NormalState("EndBlock", timestamp, 0)
        #person.append_state(state)
        self.total_processed += 1

        # Aggiorna le statistiche del giorno corrente
        self._update_stats(person)

        return []

    def finalize(self):
        """Scrive i dati finali e chiude il file."""
        self._flush_day()

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
