from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
import json


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
        self.daily_stats = {}                # dizionario con stats per giorno
        self.total_processed = 0

    def _flush_day(self):
        """Scrive le statistiche aggregate del giorno corrente su file e resetta la struttura."""
        if self.workingDate is None or not self.daily_stats:
            return

        output = {
            "type": "daily_summary",
            "date": self.workingDate.isoformat(),
            "stats": self.daily_stats
        }
        self.file_handle.write(json.dumps(output) + '\n')
        self.file_handle.flush()
        self.daily_stats = {}

    def _update_stats(self, person: Person):
        """Aggiorna le statistiche del giorno corrente con i dati di una persona."""
        for state in person.states:
            queue = state.name
            duration = 0
            if state.service_end_time and state.enqueue_time:
                duration = (state.service_end_time - state.enqueue_time).total_seconds()

            if queue not in self.daily_stats:
                self.daily_stats[queue] = {
                    "count": 1,
                    "total_time": duration,
                    "avg_time": duration
                }
            else:
                stat = self.daily_stats[queue]
                stat["count"] += 1
                stat["total_time"] += duration
                stat["avg_time"] = stat["total_time"] / stat["count"]

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
        state = NormalState("EndBlock", timestamp, 0)
        person.append_state(state)
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
