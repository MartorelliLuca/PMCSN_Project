from desPython import rngs, rvgs
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime, timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.ExponentialService import ExponentialService
from simulation.blocks.StartBlock import StartBlock
from simulation.blocks.InvioDiretto import InvioDiretto
from simulation.blocks.CompilazionePrecompilata import CompilazionePrecompilata
from simulation.blocks.InValutazioneCodaPrioritaNP import InValutazioneCodaPrioritaNP
from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.Instradamento import Instradamento

from pathlib import Path
import json


class SimulationEngine:
    """Versione migliorativa con coda prioritaria NP."""

    def getArrivalsRatesToInfinite(self) -> list[float]:
        conf_path = Path(__file__).resolve().parents[2] / "conf" / "arrival_rate.json"
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return [float(data["arrival_rate"])] * 300

    def getArrivalsRates(self) -> list[float]:
        conf_path = Path(__file__).resolve().parents[2] / "conf" / "dataset_arrivals.json"
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return [float(day["lambda_per_sec"]) for day in data.get("days", []) if "lambda_per_sec" in day]

    _REGISTRY = {
        "inValutazione": (InValutazioneCodaPrioritaNP, ("name", "dipendenti","pratichePerDipendente", "mean", "variance", "successProbability")),
        "compilazionePrecompilata": (CompilazionePrecompilata, ("name", "serversNumber", "mean", "variance", "successProbability")),
        "invioDiretto": (InvioDiretto, ("name", "mean", "variance")),
        "instradamento": (Instradamento, ("name", "serviceRate", "serversNumber", "queueMaxLenght")),
        "autenticazione": (Autenticazione, ("name", "serviceRate", "serversNumber", "successProbability", "compilazionePrecompilataProbability")),
    }

    _FIELD_ALIASES = {
        "instradamento": {"queueMaxLength": "queueMaxLenght"}
    }

    def _normalize_section(self, data: dict, section_name: str) -> dict:
        data = dict(data)
        for alias, target in self._FIELD_ALIASES.get(section_name, {}).items():
            if alias in data and target not in data:
                data[target] = data.pop(alias)
        return data

    def _instantiate(self, cfg: dict, key: str):
        cls, fields = self._REGISTRY[key]
        data = self._normalize_section(cfg[key], key)
        return cls(**{f: data[f] for f in fields})

    def buildBlocks(self):
        cfg_path = Path(__file__).resolve().parents[2] / "conf" / "input.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)

        endBlock = EndBlock()
        inValutazioneCodaPrioritariaNP = self._instantiate(cfg, "inValutazione")  # Use the JSON field name
        compilazionePrecompilata = self._instantiate(cfg, "compilazionePrecompilata")
        invioDiretto = self._instantiate(cfg, "invioDiretto")
        instradamento = self._instantiate(cfg, "instradamento")
        autenticazione = self._instantiate(cfg, "autenticazione")

        start_date = datetime.fromisoformat(cfg["date"]["start"])
        end_date   = datetime.fromisoformat(cfg["date"]["end"]) + timedelta(days=1)

        startingBlock = StartBlock(
            "Start",
            start_timestamp=datetime.combine(start_date, datetime.min.time()),
            end_timestamp=datetime.combine(end_date, datetime.min.time())
        )

        # Wiring
        startingBlock.setNextBlock(instradamento)
        instradamento.setQueueFullFallBackBlock(endBlock)
        inValutazioneCodaPrioritariaNP.setInstradamento(instradamento)
        autenticazione.setInstradamento(instradamento)
        autenticazione.setCompilazione(compilazionePrecompilata)
        autenticazione.setInvioDiretto(invioDiretto)
        compilazionePrecompilata.setNextBlock(inValutazioneCodaPrioritariaNP)
        invioDiretto.setNextBlock(inValutazioneCodaPrioritariaNP)
        inValutazioneCodaPrioritariaNP.setEnd(endBlock)
        instradamento.setNextBlock(autenticazione)
        endBlock.setStartBlock(startingBlock)

        return startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazioneCodaPrioritariaNP, endBlock

    def normale(self, daily_rates: list[float] = None):
        rngs.plantSeeds(1)
        self.event_queue = EventQueue()

        startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazioneCodaPrioritariaNP, endBlock = self.buildBlocks()

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
