from interfaces.SimBlockInterface import SimBlockInterface
from datetime import datetime, timedelta, date
from models.person import Person
from simulation.Event import Event
from simulation.states.NormalState import NormalState
from desPython import rvgs

class StartBlock(SimBlockInterface):
    """Rappresenta un blocco di partenza che genera persone con un tempo di servizio esponenziale.
    Questo blocco inizia la simulazione generando una persona e avviando il processo di creazione degli utenti.
    Per ora è molto semplice, genero persone finché il tempo simulato è prima della data finale di simulazione.
    Il tasso di servizio varia di giorno in giorno, secondo un array fornito in input (`daily_rates`).
    Il blocco successivo è specificato al momento della creazione.
    Ogni volta che viene generato un utente si crea un evento per generare il successivo.
    """

    def __init__(self, name, start_timestamp: datetime, end_timestamp:datetime):
        """Inizializza un nuovo blocco di partenza.
        
        Args:
            name (str): Il nome del blocco di partenza.
            nextBlock (SimBlockInterface): Il blocco successivo nella catena di servizi.
            start_timestamp (datetime): Il timestamp di inizio della simulazione.
            daily_rates (list[float]): Una lista di tassi medi giornalieri per ogni giorno della simulazione (dal 1 maggio al 30 settembre).
        """
        self.name = name
        self.next = None
        self.generated = 0
        self.nextBlock = None
        self.start_timestamp = start_timestamp                    # timestamp iniziale della simulazione
        self.current_time = start_timestamp                       # tempo corrente nella simulazione
        self.end_timestamp = end_timestamp    # tempo finale della simulazione (30 settembre incluso)
        self.daily_rates = None                            # array di tassi medi giornalieri
        self.entrate_nel_sistema=[0]*self.get_index_for_date(end_timestamp)  # array per tenere traccia degli arrivi giornalieri
        self.last_date = None                              # per tracciare il cambio di data

    def setDailyRates(self, daily_rates: list[float]):
        """Imposta i tassi medi giornalieri per la simulazione.
        
        Args:
            daily_rates (list[float]): Lista di tassi medi giornalieri, uno per ciascun giorno della simulazione.
        """
        self.daily_rates = daily_rates


    def get_entrate_nel_sistema(self,date:datetime):
        """Restituisce il numero di persone entrate nel sistema in un giorno specifico.
        
        Args:
            date (datetime): La data per cui si vogliono conoscere le entrate nel sistema.

        Returns:
            int: Il numero di persone entrate nel sistema in quella data.
        """
        index = self.get_index_for_date(date)
        if 0 <= index < len(self.entrate_nel_sistema):
            return self.entrate_nel_sistema[index]
        return 0


    def setNextBlock(self, nextBlock: SimBlockInterface):
        """Imposta il blocco successivo da chiamare."""
        self.nextBlock = nextBlock

    def getServiceTime(self, time: datetime) -> datetime:
        """Calcola il tempo di servizio esponenziale a partire da un timestamp specificato, usando il tasso giornaliero.
        
        Args:
            time (datetime): Il timestamp di inizio del servizio.   
        
        Returns:
            datetime: Il timestamp di fine del servizio, calcolato aggiungendo un tempo esponenziale al timestamp di inizio.
        """
        day_rate = self.getDailyRateForDate(time)
        if day_rate <= 0:
            day_rate = 1.0  # fallback per evitare errori

        exp = rvgs.Exponential(1 / day_rate)
        return time + timedelta(seconds=exp)


    def get_index_for_date(self, date_obj: datetime) -> int:
        """Restituisce l'indice del giorno per una data specifica tra 1 maggio e 30 settembre.
        
        Args:
            date_obj (datetime): La data di cui si vuole conoscere l'indice.
        
        Returns:
            int: L'indice del giorno (0 per il 1 maggio, 121 per il 30 settembre).
        """
        base_date = self.start_timestamp
        return (date_obj.date() - base_date.date()).days
    

    def getDailyRateForDate(self, date_obj: datetime) -> float:
        """Restituisce il tasso giornaliero associato a una data specifica tra 1 maggio e 30 settembre.
        
        Args:
            date_obj (datetime): La data di cui si vuole conoscere il tasso giornaliero.
        
        Returns:
            float: Il tasso di arrivo giornaliero corrispondente a quella data.
        """
        current_date = date_obj.date()
        
        # Stampa quando la data cambia
        if self.last_date is None or self.last_date != current_date:
            print(f"[{self.name}] Date changed to: {current_date}")
            self.last_date = current_date
        
        base_date = self.start_timestamp
        index = self.get_index_for_date(date_obj)
        if 0 <= index < len(self.daily_rates):
            return self.daily_rates[index]
        return -1.0  # Valore di fallback se la data è fuori intervallo

    def start(self):
        """Genera una nuova persona e il primo evento da cui parte il sistema.
        
        Returns:
            Event: Un evento che rappresenta l'inizio del servizio della persona generata,
                   oppure None se la data di generazione supera la data finale della simulazione.
        """
        nextServe = self.getServiceTime(self.current_time)

        # Controllo della condizione di fine: la generazione termina se il tempo supera l'ultimo giorno di settembre
        if nextServe > self.end_timestamp:
            print(f"[{self.name}] Generation complete: reached end time {self.end_timestamp}")
            return None

        self.next = Person(self.generated)
        self.generated += 1
        state = NormalState(self.name, nextServe, 0)
        state.service_end_time = nextServe
        state.service_start_time = nextServe
        self.current_time = nextServe
        self.next.set_last_state(state)

        # Salvataggio del tasso medio giornaliero in base al giorno in cui è stata generata l'entità
        day_rate = self.getDailyRateForDate(nextServe)

        return Event(nextServe, self.name, self.next, "generate_event", self.serveNext)

    def serveNext(self,person) -> list[Event]:
        """Rappresenta l'handler dell'evento, aggiunge la persona alla coda del primo blocco, e genera il prossimo evento.
        
        Returns:
            list[Event]: Una lista di eventi da processare, che contiene l'evento di inizio del servizio della prossima persona in coda se presente.
        """
        if self.next is None:
            return []

        serving = self.next
        self.next = None
        endTime = serving.get_last_state().service_end_time
        events = []
        self.entrate_nel_sistema[self.get_index_for_date(endTime)] += 1
        if self.nextBlock:
            event = self.nextBlock.putInQueue(serving, endTime)
           
            if event:
                events.extend(event)        
        # Genera il prossimo evento se non abbiamo ancora superato il tempo finale della simulazione
        if self.current_time <= self.end_timestamp:
            new_event = self.start()
            if new_event:
                events.append(new_event)
               
           
        return events if events else []
