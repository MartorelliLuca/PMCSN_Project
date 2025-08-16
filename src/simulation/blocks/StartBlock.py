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
    TODO: naturalemnte questo l'ho creato solo per testare inizialmente, quindi è da cambiare.
    """

    def __init__(self, name, nextBlock: SimBlockInterface, start_timestamp: datetime, daily_rates: list[float]):
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
        self.nextBlock = nextBlock
        self.start_timestamp = datetime(2025,5,1,0,0,0)                    # timestamp iniziale della simulazione
        self.current_time = start_timestamp                       # tempo corrente nella simulazione
        self.end_timestamp = datetime(2025, 5, 3,0,0,0)    # tempo finale della simulazione (30 settembre incluso)
        self.daily_rates = daily_rates                            # array di tassi medi giornalieri

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

    def getDailyRateForDate(self, date_obj: datetime) -> float:
        """Restituisce il tasso giornaliero associato a una data specifica tra 1 maggio e 30 settembre.
        
        Args:
            date_obj (datetime): La data di cui si vuole conoscere il tasso giornaliero.
        
        Returns:
            float: Il tasso di arrivo giornaliero corrispondente a quella data.
        """
        base_date = self.start_timestamp
        index = (date_obj.date() - base_date.date()).days
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
        print(f"[{self.name}] Created entity #{self.generated} on {nextServe.date()} with daily rate {day_rate:.4f}")

        return Event(nextServe, self.name, self.next, "generated_event", self.serveNext)

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

        if self.nextBlock:
            print(endTime)
            event = self.nextBlock.putInQueue(serving, endTime)
           
            if event:
                events.extend(event)

        
        # Genera il prossimo evento se non abbiamo ancora superato il tempo finale della simulazione
        if self.start_timestamp <= self.end_timestamp:
            new_event = self.start()
            if new_event:
                events.append(new_event)

        return events if events else []
