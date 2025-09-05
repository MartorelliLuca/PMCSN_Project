from desPython import rngs, rvgs
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime, timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.StartBlock import StartBlock
from simulation.verification.blocks.InvioDirettoExp import InvioDiretto
from simulation.verification.blocks.CompilazionePrecompilataExp import CompilazionePrecompilataExponential
from simulation.verification.InValutazionePrioritaExp import InValutazioneCodaPrioritaNP
from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.Instradamento import Instradamento

import json
from math import sqrt
from pathlib import Path
from tabulate import tabulate
from math import sqrt

from batchMean import read_stats, computeBatchMeans, computeBatchStdev, getStudent



class SimulationEngine:
    """Gestisce l'esecuzione della simulazione con tutti i blocchi multi-server esponenziali,
    con calcolo del tempo medio in coda per code a priorità."""

    _REGISTRY = {
        "inValutazione":            (InValutazioneCodaPrioritaNP, ("name", "serversNumber", "mean", "variance", "successProbability")),
        "compilazionePrecompilata": (CompilazionePrecompilataExponential, ("name", "serversNumber", "mean", "variance", "successProbability")),
        "invioDiretto":             (InvioDiretto, ("name", "mean", "variance")),
        "instradamento":            (Instradamento, ("name", "serviceRate", "serversNumber", "queueMaxLenght")),
        "autenticazione":           (Autenticazione, ("name", "serviceRate", "serversNumber", "successProbability", "compilazionePrecompilataProbability")),
    }

    _FIELD_ALIASES = {
        "instradamento": {"queueMaxLength": "queueMaxLenght"}
    }

    def _get_conf_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[3] / "conf" / filename

    def _normalize_section(self, data: dict, section_name: str) -> dict:
        data = dict(data)
        for alias, target in self._FIELD_ALIASES.get(section_name, {}).items():
            if alias in data and target not in data:
                data[target] = data.pop(alias)
        return data

    def _instantiate(self, cfg: dict, key: str):
        if key not in cfg:
            raise KeyError(f"Manca la sezione '{key}' nel JSON.")
        cls, fields = self._REGISTRY[key]
        data = self._normalize_section(cfg[key], key)
        missing = [f for f in fields if f not in data]
        if missing:
            raise ValueError(f"Nella sezione '{key}' mancano i campi: {missing}")
        instance = cls(**{f: data[f] for f in fields})
        
        # Modifica: inizializza lista per tempi in coda solo se è una coda a priorità
        if key == "inValutazione":
            instance.queue_times = []
        return instance

    def getArrivalsRatesToInfinite(self) -> list[float]:
        conf_path = self._get_conf_path("arrival_rate.json")
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")
        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        rate = float(data["arrival_rate"])
        return [rate] * 300

    def getArrivalsRates(self) -> list[float]:
        conf_path = self._get_conf_path("dataset_arrivals.json")
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")
        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        days = data.get("days", [])
        return [float(day["lambda_per_sec"]) for day in days if "lambda_per_sec" in day]

    def buildBlocks(self):
        cfg_path = self._get_conf_path("inputVerf.json")
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Blocchi
        endBlock                 = EndBlock()
        inValutazione            = self._instantiate(cfg, "inValutazione")
        compilazionePrecompilata = self._instantiate(cfg, "compilazionePrecompilata")
        invioDiretto             = self._instantiate(cfg, "invioDiretto")
        instradamento            = self._instantiate(cfg, "instradamento")
        autenticazione           = self._instantiate(cfg, "autenticazione")

        # Date
        start_date = datetime.fromisoformat(cfg["date"]["start"])
        end_date   = datetime.fromisoformat(cfg["date"]["end"]) + timedelta(days=1)

        startingBlock = StartBlock(
            "Start",
            start_timestamp=datetime.combine(start_date, datetime.min.time()),
            end_timestamp=datetime.combine(end_date, datetime.min.time())
        )

        # Wiring blocchi
        startingBlock.setNextBlock(instradamento)
        instradamento.setQueueFullFallBackBlock(endBlock)
        inValutazione.setInstradamento(instradamento)
        inValutazione.setEnd(endBlock)
        compilazionePrecompilata.setNextBlock(inValutazione)
        invioDiretto.setNextBlock(inValutazione)
        autenticazione.setInstradamento(instradamento)
        autenticazione.setCompilazione(compilazionePrecompilata)
        autenticazione.setInvioDiretto(invioDiretto)
        instradamento.setNextBlock(autenticazione)
        endBlock.setStartBlock(startingBlock)

        return startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazione, endBlock

    def normale(self, daily_rates: list[float] = None):
        rngs.plantSeeds(1)
        self.event_queue = EventQueue()

        startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocks()

        if daily_rates is None:
            daily_rates = self.getArrivalsRates()

        startingBlock.setDailyRates(daily_rates)
        startingBlock.setNextBlock(instradamento)
        self.event_queue.push(startingBlock.start())

        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            event = event[0] if isinstance(event, list) else event
            if event.handler:
                # Modifica: registra il tempo di entrata/uscita in coda
                if hasattr(event.person, "enter_queue_time") and hasattr(event.handler.__self__, "queue_times"):
                    handler_block = event.handler.__self__
                    if getattr(event.person, "enter_queue_time", None) is None:
                        # Persona entra in coda
                        event.person.enter_queue_time = event.timestamp
                    else:
                        # Persona esce dalla coda
                        time_in_queue = (event.timestamp - event.person.enter_queue_time).total_seconds()
                        handler_block.queue_times.append(time_in_queue)
                        event.person.enter_queue_time = None  # reset

                new_events = event.handler(event.person)
                if new_events:
                    for new_event in new_events:
                        self.event_queue.push(new_event)

        endBlock.finalize()

        # Salva riferimento al blocco con priorità per analisi
        self.inValutazione = inValutazione

    def average_queue_time(self, queue_block):
        """Calcola il tempo medio in coda per un blocco a priorità."""
        if not hasattr(queue_block, "queue_times") or not queue_block.queue_times:
            return None
        return sum(queue_block.queue_times) / len(queue_block.queue_times)
    
    def load_service_daily_stats(self, filename="transient_analysis_json/daily_stats.json"):
        service_stats = {}
    
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                data = json.loads(line)
            
            # Skip metadata lines
                if data.get('type') != 'daily_summary':
                    continue
                
                stats = data.get('stats', {})
            
                for service_name, service_data in stats.items():
                
                    if service_name == 'InValutazione':
                    # Handle priority queues in InValutazione
                        visited = service_data.get('visited', {})
                        queue_time = service_data.get('queue_time', {})
                        execution_time = service_data.get('executing_time', {})
                    
                        if isinstance(visited, dict):
                        # Multiple priority queues
                            for priority, visit_count in visited.items():
                                full_service_name = f"InValutazione_{priority}"
                            
                            # Initialize if not exists
                                if full_service_name not in service_stats:
                                    service_stats[full_service_name] = {
                                        'visited': [],
                                        'queue_time': [],
                                        'execution_time': []
                                    }
                            
                            # Add daily values
                                service_stats[full_service_name]['visited'].append(visit_count)
                                service_stats[full_service_name]['queue_time'].append(
                                    queue_time.get(priority, 0.0)
                                )
                                service_stats[full_service_name]['execution_time'].append(
                                    execution_time.get(priority, 0.0)
                                )
                        else:
                        # Single queue (fallback for old format)
                            if 'InValutazione' not in service_stats:
                                service_stats['InValutazione'] = {
                                    'visited': [],
                                    'queue_time': [],
                                    'execution_time': []
                                }
                        
                            service_stats['InValutazione']['visited'].append(visited)
                            service_stats['InValutazione']['queue_time'].append(
                                service_data.get('queue_time', 0.0)
                            )
                            service_stats['InValutazione']['execution_time'].append(
                                service_data.get('executing_time', 0.0)
                            )
                        
                    else:
                    # Handle regular services (single queue)
                        if service_name not in service_stats:
                            service_stats[service_name] = {
                                'visited': [],
                                'queue_time': [],
                                'execution_time': []
                            }
                    
                        service_stats[service_name]['visited'].append(
                            service_data.get('visited', 0)
                        )
                        service_stats[service_name]['queue_time'].append(
                            service_data.get('queue_time', 0.0)
                        )
                        service_stats[service_name]['execution_time'].append(
                            service_data.get('executing_time', 0.0)
                        )
    
        return service_stats


    



    def run_and_analyze(self, daily_rates=None, n=64*200, batch_count=8,
                    theo_json="theo_values.json",
                    stats_file="transient_analysis_json/daily_stats.json"):
        """Esegue simulazione, analisi batch e calcola tempo medio in coda."""

    # 1) Esegui la simulazione
        self.normale(daily_rates)

    # 2) Carica statistiche giornaliere invece di read_stats
        stats_raw = self.load_service_daily_stats(stats_file)

    # ------------------ STAMPA SERVIZIO PER SERVIZIO ------------------
        print("\n=== Statistiche giornaliere dei servizi ===")
        for service, metrics in stats_raw.items():
            print(f"\n📌 Servizio: {service}")
            for metric, values in metrics.items():
                print(f"   {metric}: {values}")
    # ------------------------------------------------------------------

    # 3) Riformatta stats_raw nel formato { "Service:metric": [valori,...] }
        stats = {}
        for service_name, service_data in stats_raw.items():
            queue_vals = service_data.get("queue_time", [])
            exec_vals = service_data.get("execution_time", [])

        # Queue time
            if queue_vals:
                stats[f"{service_name}:queue_time"] = queue_vals

        # Service time (execution_time → service_time)
            if exec_vals:
                stats[f"{service_name}:service_time"] = exec_vals

        # Response time (queue + service)
            if queue_vals and exec_vals:
                min_len = min(len(queue_vals), len(exec_vals))
                resp_vals = [queue_vals[i] + exec_vals[i] for i in range(min_len)]
                stats[f"{service_name}:response_time"] = resp_vals

    # 4) Carica valori teorici
        theo_path = self._get_conf_path(theo_json)
        with theo_path.open("r", encoding="utf-8") as f:
            theo_values = json.load(f)

        rows = []

    # 5) Confronto simulazione vs teorici
        for service, metrics in theo_values.items():
            for metric, theo_val in metrics.items():
                key = f"{service}:{metric}"

                if key in stats:
                    values = stats[key]
                    batch_means = computeBatchMeans(values, batch_count)
                    k_eff = len(batch_means)
                    if k_eff < 2:
                        mean_sim = None
                        ci = (None, None)
                    else:
                        mean_sim = sum(batch_means) / k_eff
                        var_sim = sum((x - mean_sim) ** 2 for x in batch_means) / (k_eff - 1)
                        se = sqrt(var_sim / k_eff)
                        tcrit = getStudent(k_eff)
                        ci = (mean_sim - tcrit * se, mean_sim + tcrit * se)
                else:
                    mean_sim = None
                    ci = (None, None)

                check = mean_sim is not None and ci[0] <= theo_val <= ci[1]

                rows.append([
                    service,
                    metric,
                    f"{theo_val:.4f}" if theo_val is not None else "-",
                    f"{mean_sim:.4f}" if mean_sim is not None else "-",
                    f"[{ci[0]:.4f}, {ci[1]:.4f}]" if mean_sim is not None else "-",
                    "✅" if check else "❌"
                ])

    # 6) Tempo medio in coda InValutazione
        avg_time_in_queue = self.average_queue_time(self.inValutazione)
        print(f"\n⏱ Tempo medio in coda InValutazione: {avg_time_in_queue:.2f} secondi"
              if avg_time_in_queue else "Nessun dato coda")

    # 7) Stampa tabellare finale
        print("\n=== Confronto simulazione vs valori teorici ===")
        services = {}
        for row in rows:
            service = row[0]
            if service not in services:
                services[service] = []
            services[service].append(row[1:])
        for service, metrics in services.items():
            print(f"\n📌 Servizio: {service}")
            print(tabulate(
                metrics,
                headers=["Metrica", "Teorico", "Simulato", "95% CI", "Coerente?"],
                tablefmt="fancy_grid"
            ))

        return rows
