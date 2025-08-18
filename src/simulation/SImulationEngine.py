from desPython import rng,rngs,rvgs
from simulation.states.NormalState import NormalState
from simulation.EventQueue import EventQueue
from models.person import Person
from datetime import datetime, date
from datetime import timedelta

from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.ExponentialService import ExponentialService
from simulation.blocks.StartBlock import StartBlock
from simulation.blocks.AccettazioneDiretta import AccettazioneDiretta
from simulation.blocks.Compilazione import Compilazione
from simulation.blocks.InEsame import InEsame

from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.Instradamento import Instradamento

from pathlib import Path
import json


class SimulationEngine:
    """Gestisce l'esecuzione della simulazione, orchestrando i blocchi di servizio e gli eventi.
    Inizializza i blocchi di partenza e di fine, gestisce la coda degli eventi e processa gli eventi in ordine temporale.
    """

    
    def getArrivalsRates(self) -> list[float]:
        """
        Legge dal file ../../conf/dataset_arrivals.json i valori 'lambda_per_sec'
        e li restituisce in un array.
        """
        conf_path = Path(__file__).resolve().parents[2] / "conf" / "dataset_arrivals.json"
        if not conf_path.exists():
            raise FileNotFoundError(f"File non trovato: {conf_path}")

        with conf_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        days = data.get("days", [])
        rates = [float(day["lambda_per_sec"]) for day in days if "lambda_per_sec" in day]

        return rates


    # Registry: mappa sezione JSON -> (Classe, ordine campi se serve posizionale)
    _REGISTRY = {
        "inEsame":        (InEsame,             ("name", "servers", "mean", "variance", "probability")),
        "compilazione":   (Compilazione,        ("name", "servers", "mean", "variance", "probability")),
        "diretta":        (AccettazioneDiretta, ("name", "mean", "variance")),
        "instradamento":  (Instradamento,       ("name", "rate", "multiServiceRate", "queueMaxLenght")),
        "autenticazione": (Autenticazione,      ("name", "serviceRate", "multiServiceRate", "successProbability", "compilazionePrecompilataProbability")),
    }
    
    # Alias di chiavi "scritte meglio" -> "come le vuole il costruttore"
    _FIELD_ALIASES = {
        "instradamento": {
            "queueMaxLength": "queueMaxLenght",  # typo comune
        }
    }
    
    def _normalize_section(self, data: dict, section_name: str) -> dict:
        data = dict(data)  # copia difensiva
        for alias, target in self._FIELD_ALIASES.get(section_name, {}).items():
            if alias in data and target not in data:
                data[target] = data.pop(alias)
        return data

    def _instantiate(self, cfg: dict, key: str):
        if key not in cfg:
            raise KeyError(f"Manca la sezione '{key}' nel JSON.")

        cls, fields = self._REGISTRY[key]
        raw = cfg[key]
        data = self._normalize_section(raw, key)

        # Check campi mancanti
        missing = [f for f in fields if f not in data]
        if missing:
            raise ValueError(f"Nella sezione '{key}' mancano i campi: {missing}")

        try:
            return cls(**{f: data[f] for f in fields})
        except TypeError:
            # 2) Fallback posizionale
            try:
                return cls(*[data[f] for f in fields])
            except Exception as e2:
                raise TypeError(f"Impossibile costruire {cls.__name__} per '{key}': {e2}")
    
    def buildBlocks(self):
    
        cfg_path = Path(__file__).resolve().parents[2] / "conf" / "input.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Config non trovata: {cfg_path}")
    
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    
        try:
            endBlock       = EndBlock()
            inEsame        = self._instantiate(cfg, "inEsame")
            compilazione   = self._instantiate(cfg, "compilazione")
            diretta        = self._instantiate(cfg, "diretta")
            instradamento  = self._instantiate(cfg, "instradamento")
            autenticazione = self._instantiate(cfg, "autenticazione")
        except Exception as e:
        
            raise RuntimeError(f"Errore caricando/istanziando da {cfg_path}: {e}")

        #todo sistema sta cosa dopo uguale a cosi json
        startingBlock = StartBlock("Start", start_timestamp=datetime(2025, 5, 1, 0, 0),end_timestamp=datetime(2025, 6, 10,0,0))


        startingBlock.setNextBlock(instradamento)   
        inEsame.setInstradamento(instradamento)
        autenticazione.setInstradamento(instradamento)
        autenticazione.setCompilazione(compilazione)
        autenticazione.setAccettazioneDiretta(diretta)
        compilazione.setNextBlock(inEsame)
        diretta.setNextBlock(inEsame)
        inEsame.setEnd(endBlock)
        instradamento.setNextBlock(autenticazione)
        endBlock.setStartBlock(startingBlock)
        return startingBlock,instradamento, autenticazione, compilazione, diretta, inEsame, endBlock
    

    def normale(self):
        """Inizializza il motore di simulazione con i blocchi di partenza e fine.
        
        Args:
            toSIm (int): Numero di persone da generare nella simulazione.
        """
        self.event_queue = EventQueue()
       
        startingBlock,instradamento, autenticazione, compilazione, diretta, inEsame,endBlock=self.buildBlocks()

        daily_rates = self.getArrivalsRates()

        startingBlock.setDailyRates(daily_rates)
        startingBlock.setNextBlock(instradamento)
        startingEvent = startingBlock.start()
        self.event_queue.push(startingEvent)
        #Simulo fino alla fine
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            event=event[0] if isinstance(event, list) else event
            if event.handler:
                new_events = event.handler(event.person)
                if new_events:
                    for new_event in new_events:
                            self.event_queue.push(new_event)
        # Scrive i risultati finali in formato testuale e JSON.
        endBlock.finalize()

        #getArrivalsRate() che ti crea un array di 365 rates che decidiamo noi con lambda uguale per tutti con 200
        #ci serve per l'analisi del transitorio
        def getArrivalsRatesToInfinite(self) -> list[float]:
            """
            Legge dal file ../../conf/dataset_arrival_rate.json il valore 'arrival_rate'
            e crea un array di 300 elementi con quel valore ripetuto.
            """
            conf_path = Path(__file__).resolve().parents[2] / "conf" / "dataset_arrival_rate.json"
            if not conf_path.exists():
                raise FileNotFoundError(f"File non trovato: {conf_path}")

            with conf_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            rate = float(data["arrival_rate"])
            rates = [rate] * 300

            return rates

