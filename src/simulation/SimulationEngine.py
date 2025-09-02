from desPython import rngs, rvgs
import csv
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime, timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.ExponentialService import ExponentialService
from simulation.blocks.StartBlock import StartBlock
from simulation.blocks.InvioDiretto import InvioDiretto
from simulation.blocks.CompilazionePrecompilata import CompilazionePrecompilata
from simulation.blocks.InValutazione import InValutazione
from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.Instradamento import Instradamento

from pathlib import Path
import json


class SimulationEngine:
    """Gestisce l'esecuzione della simulazione, orchestrando i blocchi di servizio e gli eventi."""

    def getArrivalsEqualsRates(self) -> list[float]:
        """Crea un array costante di arrivi per l’analisi del transitorio o per un mese specifico."""
        month = "mean"
        if month:
            conf_path = Path(__file__).resolve().parents[2] / "conf" / "months_arrival_rate.json"
            if not conf_path.exists():
                raise FileNotFoundError(f"File non trovato: {conf_path}")
            with conf_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            key = f"{month.lower()}_arrival_rate"
            if key not in data:
                raise KeyError(f"Chiave non trovata: {key}")
            rate = float(data[key])
        else:
            conf_path = Path(__file__).resolve().parents[2] / "conf" / "arrival_rate.json"
            if not conf_path.exists():
                raise FileNotFoundError(f"File non trovato: {conf_path}")
            with conf_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            rate = float(data["arrival_rate"])
        return [rate] * 400
    

    def getAccumulationArrivals(self) -> list[float]:
        return [0.159+0.18] * 400

    def run_transient_analysis(self, n_replicas: int = 2, seed_base: int = 123456789):
        """
        Metodo delle replicazioni per analisi del transitorio.
        Ogni replica avanza di un anno rispetto alla precedente.
        """

        for rep in range(n_replicas):
            print(f"\n--- Avvio replica {rep+1}/{n_replicas} ---")
            rngs.plantSeeds(1)

            # Costruisci i blocchi con replica_id
            self.event_queue = EventQueue()
            startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocks(replica_id=rep)
            endBlock.setStartBlock(startingBlock)

            # Imposta i daily_rates costanti da arrival_rate.json
            daily_rates = self.getArrivalsEqualsRates()
            accumulationARrivals = self.getAccumulationArrivals()
            startingBlock.setDailyRates(accumulationARrivals)

            # Sposta l'intervallo temporale di 1 anno per ogni replica
            shift_years = rep
            start_date = startingBlock.start_timestamp.replace(year=startingBlock.start_timestamp.year + shift_years)
            end_date = startingBlock.end_timestamp.replace(year=startingBlock.end_timestamp.year + shift_years)
            endBlock.setWorkingStatus(True)
            accumulating = True
            finishAccumulationDate = start_date + timedelta(hours=48)
            startingBlock.start_timestamp = start_date
            startingBlock.current_time = start_date
            startingBlock.end_timestamp = end_date

            # Avvio simulazione
            self.event_queue.push(startingBlock.start())
            while not self.event_queue.is_empty():
                event = self.event_queue.pop()
                event = event[0] if isinstance(event, list) else event
                if event.handler:

                    eventdate=event.timestamp
                    if eventdate > finishAccumulationDate and accumulating:
                        print(f"--- Fine accumulo, inizio raccolta dati il {eventdate} ---")
                        rngs.plantSeeds(seed_base)
                        endBlock.setWorkingStatus(True)
                        accumulating = False    
                        startingBlock.setDailyRates(daily_rates)

                    new_events = event.handler(event.person)
                    if new_events:
                        for new_event in new_events:
                            self.event_queue.push(new_event)

            # Finalizza la replica
            endBlock.finalize()
            print(f"✅ Replica {rep+1} completata! ({start_date.date()} → {end_date.date()})")
            
            seed_base = rngs.getSeed()



    def getArrivalsRates(self) -> list[float]:
        """Legge dal dataset i valori di arrivo giornalieri."""
        conf_path = Path(__file__).resolve().parents[2] / "conf" / "dataset_arrivals.json"
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        days = data.get("days", [])
        return [float(day["lambda_per_sec"]) for day in days if "lambda_per_sec" in day]

    # Registry dei blocchi
    _REGISTRY = {
        "inValutazione":            (InValutazione,              ("name", "dipendenti","pratichePerDipendente", "mean", "variance", "successProbability")),
        "compilazionePrecompilata": (CompilazionePrecompilata,   ("name", "serversNumber", "mean", "variance", "successProbability")),
        "invioDiretto":             (InvioDiretto,               ("name", "mean", "variance")),
        "instradamento":            (Instradamento,              ("name", "serviceRate", "serversNumber", "queueMaxLenght")),
        "autenticazione":           (Autenticazione,             ("name", "serviceRate", "serversNumber", "successProbability", "compilazionePrecompilataProbability")),
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
        if key not in cfg:
            raise KeyError(f"Manca la sezione '{key}' nel JSON.")

        cls, fields = self._REGISTRY[key]
        data = self._normalize_section(cfg[key], key)

        missing = [f for f in fields if f not in data]
        if missing:
            raise ValueError(f"Nella sezione '{key}' mancano i campi: {missing}")

        return cls(**{f: data[f] for f in fields})

    def buildBlocks(self, replica_id: int = None):
        cfg_path = Path(__file__).resolve().parents[2] / "conf" / "input.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Passa il replica_id qui
        endBlock                 = EndBlock(replica_id=replica_id)
        inValutazione            = self._instantiate(cfg, "inValutazione")
        compilazionePrecompilata = self._instantiate(cfg, "compilazionePrecompilata")
        invioDiretto             = self._instantiate(cfg, "invioDiretto")
        instradamento            = self._instantiate(cfg, "instradamento")
        autenticazione           = self._instantiate(cfg, "autenticazione")

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
        inValutazione.setInstradamento(instradamento)
        autenticazione.setInstradamento(instradamento)
        autenticazione.setCompilazione(compilazionePrecompilata)
        autenticazione.setInvioDiretto(invioDiretto)
        compilazionePrecompilata.setNextBlock(inValutazione)
        invioDiretto.setNextBlock(inValutazione)
        inValutazione.setEnd(endBlock)
        instradamento.setNextBlock(autenticazione)
        endBlock.setStartBlock(startingBlock)

        return startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazione, endBlock

    def normale_single_iteration(self, daily_rates: list[float] = None):
        """Avvia la simulazione con i tassi di arrivo specificati."""
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

    def normale_with_constant_replication(self, daily_rates: list[float] = None):
        """Avvia la simulazione con i tassi di arrivo specificati."""
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

    def normale_with_replication(self, n_replicas: int = 10, seed_base: int = 123456789, daily_rates: list[float] = None):
        """
        Metodo delle replicazioni anche per la simulazione "normale".
        Ogni replica avanza di un anno rispetto alla precedente.
        """
        for rep in range(n_replicas):
            print(f"\n--- Avvio replica {rep+1}/{n_replicas} ---")
            rngs.plantSeeds(seed_base)

            # Costruisci i blocchi con replica_id
            self.event_queue = EventQueue()
            startingBlock, instradamento, autenticazione, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocks(replica_id=rep)
            endBlock.setStartBlock(startingBlock)

            startingBlock.setDailyRates(daily_rates)

            # Sposta l’intervallo temporale di 1 anno per ogni replica
            shift_years = rep
            start_date = startingBlock.start_timestamp.replace(year=startingBlock.start_timestamp.year + shift_years)
            end_date   = startingBlock.end_timestamp.replace(year=startingBlock.end_timestamp.year + shift_years)

            startingBlock.start_timestamp = start_date
            startingBlock.current_time    = start_date
            startingBlock.end_timestamp   = end_date

            # Avvio simulazione
            self.event_queue.push(startingBlock.start())
            while not self.event_queue.is_empty():
                event = self.event_queue.pop()
                event = event[0] if isinstance(event, list) else event
                if event.handler:
                    new_events = event.handler(event.person)
                    if new_events:
                        for new_event in new_events:
                            self.event_queue.push(new_event)

            # Finalizza la replica
            endBlock.finalize()
            print(f"✅ Replica {rep+1} completata! ({start_date.date()} → {end_date.date()})")

            # Aggiorna il seed per la prossima replica
            seed_base = rngs.getSeed()
