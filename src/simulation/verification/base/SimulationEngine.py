from desPython import rngs, rvgs
import csv, math, sys 
from simulation.EventQueue import EventQueue
from datetime import datetime, timedelta
from pathlib import Path
import json
from tabulate import tabulate


# ===== Blocchi =====
from simulation.blocks.StartBlock import StartBlock
from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.EndBlockModificato import EndBlockModificato

# ===== Blocchi ESPONENZIALI =====
from simulation.verification.base.InValutazioneExp import InValutazioneExponential
from simulation.verification.base.CompilazionePrecompilataExp import CompilazionePrecompilataExponential
from simulation.verification.base.InvioDirettoExp import InvioDiretto

from typing import Optional, Tuple
from batchMean import read_stats, computeBatchMeans, getStudent

# ===== Giorni per mese =====
monthDays = {
    "may": 31,
    "june": 30,
    "july": 31,
    "august": 31,
    "september": 30
}


class SimulationEngineExp:
    """
    Simulation Engine per blocchi a SERVIZIO ESPONENZIALE
    Compatibile con verifica teorica M/M/c
    """

    def __init__(self):
        self.stream = 66

    # =========================================================
    # ARRIVI COSTANTI (TRANSITORIO)
    # =========================================================
    def getArrivalsEqualsRates(self) -> list[float]:
        month = "may_june"
        conf_path = Path(__file__).resolve().parents[4] / "conf" / "months_arrival_rate.json"
        print("SimulationEngine.py caricato!")
        print("Path JSON:", Path(__file__).resolve().parents[4] / "conf" / "months_arrival_rate.json")


        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        rate = float(data[month])
        return [rate] * 120

    def getAccumulationArrivals(self) -> list[float]:
        return [0.159 + 0.18] * 120

    # =========================================================
    # GENERAZIONE ARRIVI GIORNALIERI
    # =========================================================
    def generateLambda_low_var(
        self,
        base_rate: float,
        cv: float = 0.20,
        clip: Optional[Tuple[float, float]] = (0.6, 1.6)
    ) -> float:


        rngs.selectStream(self.stream)
        sigma2 = math.log(1.0 + cv * cv)
        sigma = math.sqrt(sigma2)
        z = rvgs.Normal(0.0, 1.0)

        mult = math.exp(-0.5 * sigma2 + sigma * z)

        if clip is not None:
            lo, hi = clip
            mult = max(lo, min(hi, mult))

        return base_rate * mult

    def getArrivalsRates(self, n_replicas=1, folder="default_arrivals") -> list[float]:
        conf_path = Path(__file__).resolve().parents[4] / "conf" / "months_arrival_rate.json"

        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        data.pop("mean_arrival_rate", None)
        data.pop("max_arrival_rate", None)

        rates = []
        out_path = Path(__file__).resolve().parents[2] / folder / f"generated_daily_arrivals_{n_replicas}.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["month", "day", "lambda_per_sec"])

            for month, rate in data.items():
                for day in range(monthDays[month]):

                    if month in ("may", "september"):
                        if (month == "may" and day < 15) or (month == "september" and day >= monthDays[month] - 15):
                            base = rate * 1.2
                        else:
                            base = rate * 0.8
                    else:
                        base = rate

                    lam = self.generateLambda_low_var(base_rate=base, cv=0.18)
                    rates.append(lam)
                    writer.writerow([month, day + 1, lam])

        return rates

    # =========================================================
    # REGISTRY ESPONENZIALE
    # =========================================================
    _REGISTRY = {
         "inValutazione": (
            InValutazioneExponential,
            (
                "name",
                "serversNumber",
                "mean",
                "variance",
                "successProbability",
            )
        ),
        "compilazionePrecompilata": (
            CompilazionePrecompilataExponential,
            ("name", "serversNumber", "mean", "variance","successProbability"),
        ),
        "invioDiretto": (
            InvioDiretto,
            ("name", "mean", "variance"),
        ),
        "start": (
            StartBlock,
            ("name", "precompilataProbability"),
        ),
    }

    def _instantiate(self, cfg: dict, key: str):
        if key not in cfg:
            raise KeyError(f"Manca la sezione '{key}' nel JSON")

        cls, fields = self._REGISTRY[key]
        data = cfg[key]

        missing = [f for f in fields if f not in data]
        if missing:
            raise ValueError(f"Nella sezione '{key}' mancano i campi: {missing}")

        return cls(**{f: data[f] for f in fields})

    # =========================================================
    # COSTRUZIONE BLOCCHI
    # =========================================================
    def buildBlocks(self, replica_id: int):
        cfg_path = Path(__file__).resolve().parents[4] / "conf" / "inputVerf.json"

        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)

        endBlock = EndBlock(replica_id=replica_id)

        inValutazione = self._instantiate(cfg, "inValutazione")
        compilazionePrecompilata = self._instantiate(cfg, "compilazionePrecompilata")
        invioDiretto = self._instantiate(cfg, "invioDiretto")
        startingBlock = self._instantiate(cfg, "start")

        start_date = datetime.fromisoformat(cfg["date"]["start"])
        end_date = datetime.fromisoformat(cfg["date"]["end"]) + timedelta(days=1)

        startingBlock.setStartAndEndTimestamps(
            start_timestamp=datetime.combine(start_date, datetime.min.time()),
            end_timestamp=datetime.combine(end_date, datetime.min.time()),
        )

        # Wiring
        startingBlock.setCompilazione(compilazionePrecompilata)
        startingBlock.setInvioDiretto(invioDiretto)

        compilazionePrecompilata.setNextBlock(inValutazione)
        invioDiretto.setNextBlock(inValutazione)

        inValutazione.setInvioDiretto(invioDiretto)
        inValutazione.setCompilazione(compilazionePrecompilata)
        inValutazione.setEnd(endBlock)

        endBlock.setStartBlock(startingBlock)

        return startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock

    # =========================================================
    # ESECUZIONE SINGOLA
    # =========================================================
    def run_single_iteration(self, daily_rates: list[float]):
        rngs.plantSeeds(2)
        self.event_queue = EventQueue()

        startingBlock, _, _, _, endBlock = self.buildBlocks(replica_id=0)
        startingBlock.setDailyRates(daily_rates)

        self.event_queue.push(startingBlock.start())

        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            event = event[0] if isinstance(event, list) else event

            if event.handler:
                new_events = event.handler(event.person)
                if new_events:
                    for e in new_events:
                        self.event_queue.push(e)

        endBlock.finalize()
    
    def run_and_analyze(self, daily_rates=None, n=64*200, batch_count=128, theo_json="theo_values.json"):
        """
        Esegue la simulazione, calcola batch means, stdev e intervallo di confidenza.
        Confronta i valori simulati con quelli teorici e stampa una tabella completa.
        """
    # Esegui la simulazione
        self.run_single_iteration(daily_rates)

    # Leggi i dati salvati
        stats_path = Path(__file__).resolve().parents[3] / "transient_analysis_json" / "daily_stats_rep0.json"

# legge le stats
        stats = read_stats(str(stats_path), n)
        #stats = read_stats('transient_analysis_json/daily_stats.json', n)
        n=len(stats["CompilazionePrecompilata:queue_time"])
        batch_count=32
    # Carica valori teorici

        theo_path = Path(__file__).resolve().parents[4] / "conf" / theo_json

        with theo_path.open("r", encoding="utf-8") as f:
            theo_values = json.load(f)

        rows = []
        # 🔹 Liste per accumulare i tempi di risposta simulati di tutti i servizi
        response_times_sim = []
        total_theo = 0.0


    # Per ogni servizio e metrica presenti nei valori teorici
        for service, metrics in theo_values.items():
            for metric, theo_val in metrics.items():
                key = f"{service}:{metric}"

                if key in stats:
                    values = stats[key]

                # Calcolo batch means
                    batch_means = computeBatchMeans(values, batch_count)
                    k_eff = len(batch_means)
                    if k_eff < 2:
                        mean_sim = None
                        ci = (None, None)
                    else:
                        mean_sim = sum(batch_means)/k_eff
                        var_sim = sum((x - mean_sim)**2 for x in batch_means)/(k_eff - 1)
                        se = math.sqrt(var_sim/k_eff)
                        tcrit = getStudent(k_eff)
                        ci = (mean_sim - tcrit*se, mean_sim + tcrit*se)
                else:
                    mean_sim = None
                    ci = (None, None)
                
                # 🔹 Accumula solo tempi di risposta
                if metric == "response_time":
                    total_theo += theo_val if theo_val is not None else 0.0
                    if mean_sim is not None:
                        response_times_sim.append(mean_sim)

            # Check coerenza
                check = (
                    mean_sim is not None and ci[0] <= theo_val <= ci[1]
                )

                rows.append([
                    service,
                    metric,
                    f"{theo_val:.4f}" if theo_val is not None else "-",
                    f"{mean_sim:.4f}" if mean_sim is not None else "-",
                    f"[{ci[0]:.4f}, {ci[1]:.4f}]" if mean_sim is not None else "-",
                    "✅" if check else "❌"
                ])

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

        # 🔹 Somma tempi di risposta simulati con batch means per intervallo di confidenza
        if response_times_sim:
            # Tratta l'array come "valori batch" per calcolare media, var, CI
            k_eff = len(response_times_sim)
            mean_sim_sum = sum(response_times_sim)
            var_sim_sum = sum((x - mean_sim_sum / k_eff) ** 2 for x in response_times_sim) / (k_eff - 1) if k_eff > 1 else 0
            se_sum = math.sqrt(var_sim_sum / k_eff) if k_eff > 1 else 0
            tcrit = getStudent(k_eff) if k_eff > 1 else 0
            ci_sum = (mean_sim_sum - tcrit * se_sum, mean_sim_sum + tcrit * se_sum)
            check_sum = ci_sum[0] <= total_theo <= ci_sum[1]
        else:
            mean_sim_sum = ci_sum = (None, None)
            check_sum = False
        
        print("\n=== Somma tempi di risposta (tutti i centri) ===")
        print(tabulate(
            [[f"{total_theo:.4f}", f"{mean_sim_sum:.4f}", f"[{ci_sum[0]:.4f}, {ci_sum[1]:.4f}]", "✅" if check_sum else "❌"]],
            headers=["Tempo Risposta Totale Teorico", "Tempo Risposta Totale Simulata", "95% CI", "Coerente?"],
            tablefmt="fancy_grid"
        ))

        print("\n")  # Riga vuota extra per leggibilità

        return rows
    

































