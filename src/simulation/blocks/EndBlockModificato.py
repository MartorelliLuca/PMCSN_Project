import os
from pathlib import Path
from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from simulation.states.StateWithServiceTIme import StateWithServiceTime

import json

from simulation.blocks.StartBlock import StartBlock


class EndBlockModificato(SimBlockInterface):
    """Blocco finale che raccoglie, aggrega e salva risultati giornalieri della simulazione."""

    def __init__(self, output_file="daily_stats.json", replica_id: int = None,outDirString: str = "transient_analysis_json"):
        # Directory per i file di transitorio
        out_dir = Path(__file__).resolve().parents[2] / outDirString
        os.makedirs(out_dir, exist_ok=True)

        # Se è una replica, rinomina il file
        if replica_id is not None:
            base, ext = output_file.rsplit(".", 1)
            output_file = f"{base}_rep{replica_id}.{ext}"

        self.output_file = str(out_dir / output_file)
        self.file_handle = open(self.output_file, 'w', encoding='utf-8', buffering=8192)

        # Scrive intestazione metadata
        metadata = {
            "type": "metadata",
            "replica_id": replica_id,
            "start_timestamp": datetime.now().isoformat(),
            "format": "json_lines_per_day"
        }
        self.file_handle.write(json.dumps(metadata) + '\n')
        self.file_handle.flush()

        # Variabili di stato
        self.workingDate = None
        self.daily_stats = {}
        self.day_summary = {
            "entrati": 0,
            "usciti": 0,
            "trovato_coda_piena": 0
        }
        self.total_processed = 0
        self.start_block = None
        self.pending_daily_summaries = []
        self.working = True
        # Support per-date accumulators because completions may arrive out-of-order
        # Keys are datetime.date objects
        self.daily_stats_by_date = {}
        self.day_summary_by_date = {}


    def setWorkingStatus(self, status: bool):
        self.working = status

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
    

    def _update_stats(self, person: Person, completion_date):
        """Aggiorna le statistiche del giorno (completion_date) con i dati di una persona.

        We use per-date buckets because completions may arrive out-of-order.
        """
        last_state = person.get_last_state()
        startState= person.states[0].get_queue_exit_time().date()
        
        # Ensure per-date accumulators exist
        daily_stats = self.daily_stats_by_date.setdefault(startState, {})
        day_summary = self.day_summary_by_date.setdefault(startState, {
            "entrati": 0,
            "usciti": 0,
            "trovato_coda_piena": 0
        })
        day_summaryEnd= self.day_summary_by_date.setdefault(completion_date, {
            "entrati": 0,
            "usciti": 0,
            "trovato_coda_piena": 0
        })
        day_summaryEnd["usciti"] += 1
        for state in person.states:
            queue = state.name
            if queue == "Start":
                continue

            time_in_queue = (state.service_start_time - state.enqueue_time).total_seconds() if state.service_start_time else None
            time_executing = (state.service_end_time - state.service_start_time).total_seconds() if state.service_start_time else None
            in_code = state.queue_length if state.queue_length else 0

            if state and isinstance(state, StateWithServiceTime):
                if queue not in daily_stats:
                    daily_stats[queue] = {
                        "visited": {state.get_queue_name(): 1},
                        "queue_time": {state.get_queue_name(): time_in_queue},
                        "executing_time": {state.get_queue_name(): time_executing},
                        "queue_lenght": {state.get_queue_name(): in_code},
                        "data": {
                            "queue_time": [time_in_queue,],
                            "queue_lenght": [in_code,],
                            "executing_time": [time_executing,],
                        }
                    }
                elif state.get_queue_name() not in daily_stats[queue].get("visited", {}):
                    stat = daily_stats[queue]
                    stat["visited"][state.get_queue_name()] = 1
                    stat["queue_time"][state.get_queue_name()] = time_in_queue
                    stat["executing_time"][state.get_queue_name()] = time_executing
                    stat["queue_lenght"][state.get_queue_name()] = in_code
                    if len(stat["data"]["queue_time"]) < 50*50 and stat["visited"] % 6 == 0:
                        stat["data"]["queue_time"].append(time_in_queue)
                        stat["data"]["queue_lenght"].append(in_code)
                        stat["data"]["executing_time"].append(time_executing)
                else:
                    stat = daily_stats[queue]
                    stat["visited"][state.get_queue_name()] += 1
                    stat["queue_time"][state.get_queue_name()] += time_in_queue
                    stat["executing_time"][state.get_queue_name()] += time_executing
                    stat["queue_lenght"][state.get_queue_name()] += in_code
                    if len(stat["data"]["queue_time"]) < 50*50 and stat["visited"] % 6 == 0:
                        stat["data"]["queue_time"].append(time_in_queue)
                        stat["data"]["queue_lenght"].append(in_code)
                        stat["data"]["executing_time"].append(time_executing)
            else:
                if queue not in daily_stats:
                    daily_stats[queue] = {
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
                    stat = daily_stats[queue]
                    stat["visited"] += 1
                    stat["queue_time"] += time_in_queue
                    stat["queue_lenght"] += in_code
                    stat["executing_time"] += time_executing
                    if stat["visited"] < 25*50 and stat["visited"] % 6 == 0:
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

        if self.working is False:
            return []
        completion_date = timestamp.date()

        # Salva stato finale
        #state = NormalState("EndBlock", timestamp, 0)
        #person.append_state(state)
        self.total_processed += 1

        # Aggiorna le statistiche per la data di completamento
        self._update_stats(person, completion_date)

        return []

    def _flush_all_dates(self):
        """Process all buffered per-date accumulators and append summaries to pending buffer."""
        if not self.daily_stats_by_date:
            return

        for date in sorted(self.daily_stats_by_date.keys()):
            stats = self.daily_stats_by_date[date]
            day_summary = self.day_summary_by_date.get(date, {
                "entrati": 0,
                "usciti": 0,
                "trovato_coda_piena": 0
            })

            day_summary["entrati"] = self.get_entrate_nel_sistema(date)

            # finalize averages
            for queue, s in stats.items():
                if isinstance(s.get("visited"), dict):
                    for queue_name, visited_count in s["visited"].items():
                        if visited_count > 0:
                            s["queue_time"][queue_name] /= visited_count
                            s["queue_lenght"][queue_name] /= visited_count
                            s["executing_time"][queue_name] /= visited_count
                        else:
                            s["queue_time"][queue_name] = 0
                            s["queue_lenght"][queue_name] = 0
                            s["executing_time"][queue_name] = 0
                else:
                    if s.get("visited", 0) > 0:
                        s["queue_time"] /= s["visited"]
                        s["queue_lenght"] /= s["visited"]
                        s["executing_time"] /= s["visited"]
                    else:
                        s["queue_time"] = 0
                        s["queue_lenght"] = 0
                        s["executing_time"] = 0

            output = {
                "type": "daily_summary",
                "date": date.isoformat(),
                "summary": day_summary,
                "stats": stats
            }

            self.pending_daily_summaries.append(output)

        # clear
        self.daily_stats_by_date = {}
        self.day_summary_by_date = {}

    def finalize(self):
        """Scrive i dati finali e chiude il file."""
        # Ensure all per-date stats are processed and buffered
        self._flush_all_dates()

        # Write all buffered daily summaries in one pass
        for summary in self.pending_daily_summaries:
            self.file_handle.write(json.dumps(summary) + '\n')
        self.file_handle.flush()

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