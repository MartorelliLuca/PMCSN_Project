import heapq
class EventQueue:
    """Gestisce una coda di eventi per la simulazione.
    Utilizza un heap per mantenere gli eventi ordinati in base al timestamp.
    (heap inteso come struttura dati, non come memoria)
    """
    def __init__(self):
        """Inizializza una nuova coda di eventi vuota."""
        self.events = []

    def push(self, event):
        """Aggiunge un evento alla coda.
        
        Args:
            event (Event): L'evento da aggiungere alla coda.
        """
        heapq.heappush(self.events, event)

    def pop(self):
        """Rimuove e restituisce l'evento con il timestamp più basso.
        
        Returns:    
            Event: L'evento con il timestamp più basso.
        """
        return heapq.heappop(self.events)

    def is_empty(self):
        """Verifica se la coda di eventi è vuota.
        
        Returns:
            bool: True se la coda è vuota, False altrimenti.
        """
        return len(self.events) == 0