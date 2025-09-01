from desPython import rngs, rvgs
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime, timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.StartBlock import StartBlock
from simulation.blocks.InvioDiretto import InvioDiretto
from simulation.verification.blocks.CompilazionePrecompilataExp import CompilazionePrecompilataExponential
from simulation.verification.blocks.InValutazioneExp import InValutazioneExponential
from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.Instradamento import Instradamento

import json
from math import sqrt
from desPython import rvms
from batchMean import read_stats, computeMeanAndStdev, autocorrelation_stats, getStudent

from pathlib import Path
import json


class SimulationEngine:
    """Gestisce l'esecuzione della simulazione con tutti i blocchi multi-server esponenziali."""

    _REGISTRY = {
        "inValutazione":            (InValutazioneExponential, ("name", "serversNumber", "mean", "variance", "successProbability")),
        "compilazionePrecompilata": (CompilazionePrecompilataExponential, ("name", "serversNumber", "mean", "variance", "successProbability")),
        "invioDiretto":             (InvioDiretto, ("name", "mean", "variance")),
        "instradamento":            (Instradamento, ("name", "serviceRate", "serversNumber", "queueMaxLenght")),
        "autenticazione":           (Autenticazione, ("name", "serviceRate", "serversNumber", "successProbability", "compilazionePrecompilataProbability")),
    }

    _FIELD_ALIASES = {
        "instradamento": {"queueMaxLength": "queueMaxLenght"}
    }

    def _get_conf_path(self, filename: str) -> Path:
        return Path(__file__).resolve().parents[4] / "conf" / filename

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
        return cls(**{f: data[f] for f in fields})

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
                new_events = event.handler(event.person)
                if new_events:
                    for new_event in new_events:
                        self.event_queue.push(new_event)

        endBlock.finalize()

    def run_and_analyze(self, daily_rates=None, n=64*100, batch_count=64, theo_json="theo_values.json"):
        """
        Esegue la simulazione e calcola batch means, stdev e intervallo di confidenza.
        Verifica anche la coerenza con i valori teorici specificati in un file JSON.
        """
        # Esegui la simulazione
        self.normale(daily_rates)

        # Leggi i dati salvati
        stats = read_stats('daily_stats.json', n)

        # Carica valori teorici
        theo_path = self._get_conf_path(theo_json)
        with theo_path.open("r", encoding="utf-8") as f:
            theo_values = json.load(f)

        print(f"[DEBUG] Ho letto {len(stats)} servizi da daily_stats.json: {list(stats.keys())}")
    

        # Calcolo batch means e stdev
        batchesMean = {}
        batchesStdev = {}
        for service, data in stats.items():
            mean, std = computeMeanAndStdev(data, batch_count)
            batchesMean[service] = mean
            batchesStdev[service] = std

        # Autocorrelazione e verifica vs valori teorici
        results = {}
        for service, batch_means in batchesMean.items():
            mean_sim, stddev = autocorrelation_stats(20, batch_means)
            student = getStudent(batch_count)
            ci = student * stddev / sqrt(len(batch_means))

            # Prendi i valori teorici
            queue_theoretical = theo_values[service].get("queue_time")
            service_theoretical = theo_values[service].get("service_time")
            response_theoretical = theo_values[service].get("response_time")

            # Verifica coerenza
            check_queue = queue_theoretical is None or (mean_sim - ci <= queue_theoretical <= mean_sim + ci)
            check_service = service_theoretical is None or (mean_sim - ci <= service_theoretical <= mean_sim + ci)
            check_response = response_theoretical is None or (mean_sim - ci <= response_theoretical <= mean_sim + ci)

            results[service] = {
                "mean_sim": mean_sim,
                "ci_95": (mean_sim - ci, mean_sim + ci),
                "queue_check": check_queue,
                "service_check": check_service,
                "response_check": check_response
            }

            # Stampa risultati
            print(f"\nServizio: {service}")
            print(f"Media simulata = {mean_sim:.2f}, 95% CI = [{mean_sim - ci:.2f}, {mean_sim + ci:.2f}]")
            print(f"Queue time teorico = {queue_theoretical}, coerente? {check_queue}")
            print(f"Service time teorico = {service_theoretical}, coerente? {check_service}")
            print(f"Response time teorico = {response_theoretical}, coerente? {check_response}")

        return results

