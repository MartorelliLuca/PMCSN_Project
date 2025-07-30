import models.request as Request




class Person:
    """Rappresenta una persona/entità nella simulazione.
    
    Mantiene una lista degli stati attraversati durante la simulazione.
    """
    def __init__(self, ID):
        """Inizializza una nuova persona con un ID univoco.(pero non è obbligatorio renderlo univico)"""
        self.states=[]
        self.login_time=0
        self.request_compilation_time=0
        self.request_refused=0
        self.login_failed=0
        self.ID = ID
        
    def append_state(self, state):
        """Aggiunge un nuovo stato alla lista degli stati facendo una append."""
        self.states.append(state)

    def get_last_state(self):
        """Restituisce l'ultimo stato o None se la lista è vuota."""
        if self.states:
            return self.states[-1]
        return None
    
    def set_last_state(self, state):
        """Sostituisce l'ultimo stato o lo aggiunge se la lista è vuota."""
        if self.states:
            self.states[-1] = state
        else:
            self.append_state(state)

    

    