from datetime import datetime


class StateInterface:
    """Interfaccia per gli oggetti stato nei blocchi di simulazione.
    
    Definisce i metodi minimi richiesti per ogni stato. Rappresenta il comportamento
    di una persona/richiesta all'interno di un blocco di simulazione e ne conserva lo stato.
    """

    def get_service_name(self) -> str:
        """Ottiene il nome del servizio.
        
        Returns:
            str: Il nome del servizio associato a questo stato.
        """
        pass

    def queue_length(self) -> int:
        """Ottiene la lunghezza attuale della coda.
        
        Returns:
            int: Il numero di entità attualmente in coda.
        """
        pass

    def get_queue_enter_time(self) -> datetime:
        """Ottiene il tempo di ingresso nella coda.
        
        Returns:
            datetime: Il timestamp di quando l'entità è entrata in coda.
        """
        pass

    def get_queue_exit_time(self) -> datetime:
        """Ottiene il tempo di uscita dalla coda.
        
        Returns:
            datetime: Il timestamp di quando l'entità ha lasciato la coda per iniziare il servizio.
        """
        pass

    def get_working_end(self) -> datetime:
        """Ottiene il tempo di fine del lavoro/servizio.
        
        Returns:
            datetime: Il timestamp di quando è programmata la fine del servizio.
        """
        pass    

    def get_next_event_time(self) -> datetime:
        """Ottiene il tempo del prossimo evento.
        
        Returns:
            datetime: Il timestamp del prossimo evento programmato per questo stato.
        """
        pass   

    def to_dict(self) -> dict:
        """Converte lo stato in un dizionario per la serializzazione JSON.
        
        Returns:
            dict: Rappresentazione del stato come dizionario.
        """
        pass   