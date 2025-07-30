class Event:
    """Rappresenta gli eventi che vengono creati durante la simulazione.
    In particolare, rappresenta un'azione che deve essere eseguita ad un certo timestamp.
    """

    def __init__(self, timestamp, serviceName, person,eventType,handler=None):
        """Inizializza un nuovo evento.
        
        Args:
            timestamp (datetime): Il momento in cui l'evento deve essere eseguito.
            serviceName (str): Il nome del servizio associato all'evento.
            person (Person): La persona coinvolta nell'evento.
            eventType (str): Il tipo di evento (una stringa indicativa).
            handler: Un eventuale gestore dell'evento, se necessario, è la funzione che verra chiamata quando è ora di eseguire l'evento.
        """ 
        self.timestamp = timestamp
        self.eventType = eventType  
        self.serviceName = serviceName
        self.handler = handler
        self.person = person

    def __lt__(self, other):
        """
        Confronta due eventi basandosi sul timestamp.
        Permette di ordinare gli eventi in base al momento in cui devono essere eseguiti.
        L'ordinamento non è totale, infatti due eventi con lo stesso timestamp non sono confrontabili. 
        
        Args:
            other (Event): L'altro evento da confrontare.
        """
        return self.timestamp < other.timestamp


