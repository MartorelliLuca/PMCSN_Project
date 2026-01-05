from desPython import rngs, rvgs
import csv, math
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
from simulation.blocks.InValutazioneCodaPrioritaNP import InValutazioneCodaPrioritaNP
from simulation.blocks.EndBlockModificato import EndBlockModificato


from pathlib import Path
from typing import Optional, Tuple
import json

monthDays={
    "may":31,
    "june":30,
    "july":31,
    "august":31,
    "september":30
}

class SimulationEngine:
    """Gestisce l'esecuzione della simulazione, orchestrando i blocchi di servizio e gli eventi."""
    def __init__(self):    
        self.stream=66

    def getArrivalsEqualsRates(self) -> list[float]:
        """Crea un array costante di arrivi per l’analisi del transitorio o per un mese specifico."""
        month = "may_june"
        conf_path = Path(__file__).resolve().parents[4] / "conf" / "months_arrival_rate.json"
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")
        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        rate = float(data[month])
        return [rate] * 120                         #<- qua ci mettiamo il numero di giorni per il transitorio
    

    def getAccumulationArrivals(self) -> list[float]:
        return [0.159+0.18] * 120

    def run_transient_analysis(self, n_replicas, seed_base):
        """
        Metodo delle replicazioni per analisi del transitorio.
        Ogni replica avanza di un anno rispetto alla precedente.
        """

        seeds_path = Path(__file__).resolve().parents[2] / "used_seeds.txt"
        rngs.plantSeeds(seed_base)

        for rep in range(n_replicas):
            print(f"\n--- Avvio replica {rep+1}/{n_replicas} ---")

            # Costruisci i blocchi con replica_id
            self.event_queue = EventQueue()
            startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocks(replica_id=rep)
            endBlock.setStartBlock(startingBlock)

            # Imposta i daily_rates costanti da arrival_rate.json
            daily_rates = self.getArrivalsEqualsRates()
            accumulationArrivals = self.getAccumulationArrivals()
            startingBlock.setDailyRates(accumulationArrivals)

            # Non spostiamo l'intervallo temporale: ogni replica è una run indipendente
            # che condivide la stessa finestra temporale (ma ha replica_id diverso).
            start_date = startingBlock.start_timestamp
            end_date = startingBlock.end_timestamp
            endBlock.setWorkingStatus(True)
            accumulating = True
            finishAccumulationDate = start_date + timedelta(hours=48)
            startingBlock.start_timestamp = start_date
            startingBlock.current_time = start_date
            startingBlock.end_timestamp = end_date
            with seeds_path.open("a", encoding="utf-8") as f:
                            f.write(f"Replica {rep+1}: seed = {seed_base}\n")
            # Avvio simulazione
            self.event_queue.push(startingBlock.start())
            while not self.event_queue.is_empty():
                event = self.event_queue.pop()
                event = event[0] if isinstance(event, list) else event
                if event.handler:

                    eventdate=event.timestamp
                    if eventdate > finishAccumulationDate and accumulating:
                        print(f"--- Fine accumulo, inizio raccolta dati il {eventdate} ---")
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
            
            seed_base = rngs.getSeed() #just to print it on file
    
    # --- Generatore a bassa varianza, vedi se va bene alex visto che hai detto di usare una normale---
    #def generateLambda_low_var(self, base_rate: float, cv: float = 0.20, clip: tuple[float,float] | None = (0.6, 1.6)) -> float:
    def generateLambda_low_var(
    self,
    base_rate: float,
    cv: float = 0.20,
    clip: Optional[Tuple[float, float]] = (0.6, 1.6)
    ) -> float:

        """
        Ritorna un lambda giornaliero con varianza ridotta.
        Usa un moltiplicatore lognormale con media 1 (mu = -0.5*sigma^2).
        cv ~ deviazione standard relativa del moltiplicatore (0.10-0.30 tipico).
        clip = (min,max) per tagliare outlier (None per disabilitare).
        """
        rngs.selectStream(self.stream)
        # rapporto tra varianza e media^2 del moltiplicatore = cv^2 = exp(sigma^2) - 1
        sigma2 = math.log(1.0 + cv*cv)
        sigma = math.sqrt(sigma2)
        z = rvgs.Normal(0.0, 1.0)                   # N(0,1) dal tuo rvgs
        mult = math.exp(-0.5 * sigma2 + sigma * z)  # E[mult] = 1

        if clip is not None:
            lo, hi = clip
            if mult < lo: mult = lo
            if mult > hi: mult = hi

        return base_rate * mult
    


    def _gamma_int_shape(self, k: int) -> float:
        """Gamma(shape=k, scale=1) per k intero usando Erlang(k, 1.0)."""
        # Erlang(n, b) nel tuo rvgs è Gamma(k=n, scale=b)
        return rvgs.Erlang(k, 1.0)
    

    def getArrivalsRates(self,n_replicas=1,folder="defualt_arrivals") -> list[float]:
        """Legge dal dataset i valori di arrivo giornalieri."""
        conf_path = Path(__file__).resolve().parents[2] / "conf" / "months_arrival_rate.json"#{'may_arrival_rate': 0.2736, 'june_arrival_rate': 0.1412, 'july_arrival_rate': 0.1367, 'august_arrival_rate': 0.0912, 'september_arrival_rate': 0.2825, 'mean_arrival_rate': 0.1622935, 'max_arrival_rate': 0.4447835215743806}
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print(data)
        data.pop("mean_arrival_rate", None)
        data.pop("max_arrival_rate", None)
        rates = []

        # Prepare output CSV path and ensure directory exists
        out_path = Path(__file__).resolve().parents[2] / folder / f"generated_daily_arrivals{n_replicas}.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write generated daily rates to CSV (overwrite each run)
        with out_path.open("w", encoding="utf-8", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["month", "day", "lambda_per_sec"])

            # dentro getArrivalsRates(), nel loop per i giorni del mese:
            for month, rate in data.items():
                for i in range(monthDays[month]):
                    # stagionalità come prima
                    if month == "may" or month == "september":
                        if (month == "may" and i < 15) or (month == "september" and i >= monthDays[month]-15):
                            base = rate * 1.2    # primi 15 di maggio ↑, ultimi 15 di settembre ↑
                        else:
                            base = rate * 0.8
                    else:
                        base = rate
                    
                    generated = self.generateLambda_low_var(base_rate=base, cv=0.18, clip=(0.6, 1.6))
                    #generated = self.generateLambda_ultra_low_var(base_rate=base, delta=0.08, k=80)

                    rates.append(generated)
                    writer.writerow([month, i + 1, generated])

        print(f"Wrote {len(rates)} generated daily rates to: {out_path}")
        return rates
            



        return [float(day["lambda_per_sec"]) for day in days if "lambda_per_sec" in day]

    # Registry dei blocchi
    _REGISTRY = {
        "inValutazione":            (InValutazione,              ("name", "dipendenti","pratichePerDipendente", "mean", "variance", "successProbability",
                                                                    "dropoutProbability", "precompilataProbability")),
        "inValutazione": (InValutazioneCodaPrioritaNP, ("name", "dipendenti","pratichePerDipendente", "mean", "variance", "successProbability",
                                                                    "dropoutProbability", "precompilataProbability")),
        "compilazionePrecompilata": (CompilazionePrecompilata,   ("name", "serversNumber", "mean", "variance", "successProbability")),
        "invioDiretto":             (InvioDiretto,               ("name", "mean", "variance")),
        "start":                    (StartBlock,                 ("name", "precompilataProbability")),
    }

    _FIELD_ALIASES = {}

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

    def buildBlocks(self, replica_id):
        #self.getArrivalsRates()
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
        startingBlock             = self._instantiate(cfg, "start")
        start_date = datetime.fromisoformat(cfg["date"]["start"])
        end_date   = datetime.fromisoformat(cfg["date"]["end"]) + timedelta(days=1)

        startingBlock.setStartAndEndTimestamps(
            start_timestamp=datetime.combine(start_date, datetime.min.time()),
            end_timestamp=datetime.combine(end_date, datetime.min.time())
        )

        # Wiring
        startingBlock.setCompilazione(compilazionePrecompilata)    
        startingBlock.setInvioDiretto(invioDiretto)
                

        compilazionePrecompilata.setNextBlock(inValutazione)
        invioDiretto.setNextBlock(inValutazione)
        inValutazione.setEnd(endBlock)
        inValutazione.setInvioDiretto(invioDiretto)
        inValutazione.setCompilazione(compilazionePrecompilata)
        endBlock.setStartBlock(startingBlock)

        return startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock

    def buildBlocksFinito(self, replica_id):
        #self.getArrivalsRates()
        cfg_path = Path(__file__).resolve().parents[2] / "conf" / "input.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Passa il replica_id qui
        endBlock                 = EndBlockModificato(replica_id=replica_id,outDirString="finite_horizon_json_migliorativo")
        # Use InValutazioneCodaPrioritaNP with inValutazione config
        inValutazione            = InValutazioneCodaPrioritaNP(**{f: cfg["inValutazione"][f] for f in ("name", "dipendenti","pratichePerDipendente", "mean", "variance", "successProbability", "dropoutProbability", "precompilataProbability")})
        compilazionePrecompilata = self._instantiate(cfg, "compilazionePrecompilata")
        invioDiretto             = self._instantiate(cfg, "invioDiretto")
        startingBlock             = self._instantiate(cfg, "start")
        start_date = datetime.fromisoformat(cfg["date"]["start"])
        end_date   = datetime.fromisoformat(cfg["date"]["end"]) + timedelta(days=1)

        startingBlock.setStartAndEndTimestamps(
            start_timestamp=datetime.combine(start_date, datetime.min.time()),
            end_timestamp=datetime.combine(end_date, datetime.min.time())
        )

        # Wiring
        startingBlock.setCompilazione(compilazionePrecompilata)    
        startingBlock.setInvioDiretto(invioDiretto)
                

        compilazionePrecompilata.setNextBlock(inValutazione)
        invioDiretto.setNextBlock(inValutazione)
        inValutazione.setEnd(endBlock)
        inValutazione.setInvioDiretto(invioDiretto)
        inValutazione.setCompilazione(compilazionePrecompilata)
        endBlock.setStartBlock(startingBlock)

        return startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock


    def buildBlocksSingleIteration(self):
        cfg_path = Path(__file__).resolve().parents[2] / "conf" / "input.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")

        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Passa il replica_id qui
        endBlock                 = EndBlock()
        inValutazione            = self._instantiate(cfg, "inValutazione")
        compilazionePrecompilata = self._instantiate(cfg, "compilazionePrecompilata")
        invioDiretto             = self._instantiate(cfg, "invioDiretto")
        startingBlock             = self._instantiate(cfg, "start")


        start_date = datetime.fromisoformat(cfg["date"]["start"])
        end_date   = datetime.fromisoformat(cfg["date"]["end"]) + timedelta(days=1)

        startingBlock.setStartAndEndTimestamps(
            start_timestamp=datetime.combine(start_date, datetime.min.time()),
            end_timestamp=datetime.combine(end_date, datetime.min.time())
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



    def run_finito_experiment(self, n_replicas=4, seed_base=3):

        seeds_path = Path(__file__).resolve().parents[2] / "used_seeds.txt"
        rngs.plantSeeds(seed_base)

        for rep in range(n_replicas):
            print(f"\n--- Avvio replica {rep+1}/{n_replicas} ---")

            # Scrivi il seed usato su file
            with seeds_path.open("a", encoding="utf-8") as f:
                f.write(f"Replica {rep+1}: seed = {seed_base}\n")

            # Costruisci i blocchi con replica_id
            self.event_queue = EventQueue()
            startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocksFinito(replica_id=rep)
            #endBlock.setStartBlock(startingBlock)
            daily_rates = self.getArrivalsRates(rep,"finite_horizon_json_migliorativo_arrivals")
            startingBlock.setDailyRates(daily_rates)

            # Sposta l'intervallo temporale di 1 anno per ogni replica
            shift_years = 0
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

            seed_base = rngs.getSeed() #just for printing



    def normale_single_iteration(self, daily_rates):
        """Avvia la simulazione con i tassi di arrivo specificati."""
        rngs.plantSeeds(2)
        self.event_queue = EventQueue()

        startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocksSingleIteration()

        if daily_rates is None:
            daily_rates = self.getArrivalsRates()

        startingBlock.setDailyRates(daily_rates)
        #startingBlock.setNextBlock(instradamento)
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

    def normale_with_constant_replication(self, daily_rates):
        """Avvia la simulazione con i tassi di arrivo specificati."""
        rngs.plantSeeds(2)
        self.event_queue = EventQueue()

        startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocks()

        if daily_rates is None:
            daily_rates = self.getArrivalsRates()

        startingBlock.setDailyRates(daily_rates)
        #startingBlock.setNextBlock(instradamento)
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

    def normale_with_replication(self, n_replicas, seed_base, daily_rates):
        """
        Metodo delle replicazioni anche per la simulazione "normale".
        Ogni replica avanza di un anno rispetto alla precedente.
        """
        seeds_path = Path(__file__).resolve().parents[2] / "used_seeds.txt"
        rngs.plantSeeds(seed_base)

        for rep in range(n_replicas):
            print(f"\n--- Avvio replica {rep+1}/{n_replicas} ---")

            # Scrivi il seed usato su file
            with seeds_path.open("a", encoding="utf-8") as f:
                f.write(f"Replica {rep+1}: seed = {seed_base}\n")

            # Costruisci i blocchi con replica_id
            self.event_queue = EventQueue()
            startingBlock, compilazionePrecompilata, invioDiretto, inValutazione, endBlock = self.buildBlocks(replica_id=rep)
            #endBlock.setStartBlock(startingBlock)

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

            seed_base = rngs.getSeed() #just for printing