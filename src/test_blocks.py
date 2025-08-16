from datetime import datetime
from simulation.EventQueue import EventQueue
from simulation.blocks.EndBlock import EndBlock
from simulation.blocks.StartVecchio import StartVecchio
from simulation.blocks.Instradamento import Instradamento
from simulation.blocks.Compilazione import Compilazione
from simulation.blocks.Autenticazione import Autenticazione
from simulation.blocks.AccettazioneDiretta import AccettazioneDiretta
from simulation.blocks.InEsame import InEsame


class BlockTester:
    """Test class per verificare il funzionamento dei blocchi di simulazione."""
    
    def __init__(self):
        self.event_queue = EventQueue()
    
    def test_all_blocks(self, num_persons=10):
        """Test completo di tutti i blocchi seguendo la struttura del SimulationEngine.
        
        Args:
            num_persons (int): Numero di persone da simulare (default: 10)
        """
        print(f"Iniziando test con {num_persons} persone...")
        
        # Inizializza la coda degli eventi
        self.event_queue = EventQueue()
        start_timestamp = datetime(2023, 10, 1, 0, 0, 0)
        
        # Crea i blocchi seguendo la catena logica del SimulationEngine
        print("Creazione blocchi...")
        
        # Blocco finale
        endBlock = EndBlock()
        print("✓ EndBlock creato")
        
        # Blocco InEsame - seguendo esattamente il pattern del SimulationEngine
        # ma con parametri corretti per il constructor
        inEsame = InEsame("InEsame", 2, 300, 10000, 0.5)  # name, multiServiceRate, mean, variance, accetpanceRate
        print("✓ InEsame creato")
        
        # Blocco Compilazione (chiamato "Evasione" nel SimulationEngine)
        # con parametri corretti per il constructor  
        evasione = Compilazione("Evasione", 1, 600, 14400, 0.1)  # name, multiServiceRate, mean, variance, compilationSuccessRate
        evasione.setNextBlock(inEsame)
        print("✓ Compilazione/Evasione creato")
        
        # Blocco Autenticazione - usando il constructor corretto
        autenticazione = Autenticazione(
            name="Autenticazione", 
            serviceRate=4.0,
            multiServiceRate=3,
            successProbability=0.9,
            compilazionePrecompilataProbability=0.3
        )
        print("✓ Autenticazione creato")
        
        # Blocco Instradamento - usando il constructor corretto
        instradamento = Instradamento(
            name="Instradamento", 
            rate=6.25,
            multiServiceRate=5,
            queueMaxLenght=50
        )
        instradamento.setNextBlock(autenticazione)
        instradamento.setQueueFullFallBackBlock(endBlock)
        print("✓ Instradamento creato")
        
        # AccettazioneDiretta - questo blocco deve essere collegato separatamente
        accettazioneDiretta = AccettazioneDiretta(
            name="AccettazioneDiretta",
            mean=180,  # 3 minuti
            variance=3600
        )
        accettazioneDiretta.setNextBlock(inEsame)
        print("✓ AccettazioneDiretta creato")
        
        # Imposta i riferimenti circolari necessari usando i metodi corretti
        autenticazione.setInstradasmento(instradamento)
        autenticazione.setCompilazione(evasione)
        autenticazione.setAccettazioneDiretta(accettazioneDiretta)
        
        # Imposta i riferimenti per InEsame
        inEsame.setInstradasmento(instradamento)
        inEsame.setEnd(endBlock)
        
        print("✓ Riferimenti circolari impostati")
        
        # Blocco di partenza
        startingBlock = StartVecchio(
            name="StartingBlock",
            rate=5.0,
            nextBlock=instradamento,
            start_timestamp=start_timestamp,
            toSim=num_persons
        )
        print("✓ StartVecchio creato")
        
        # Inizia la simulazione
        print("\nIniziando simulazione...")
        startingEvent = startingBlock.start()
        self.event_queue.push(startingEvent)
        
        event_count = 0
        max_events = num_persons * 20  # Limite di sicurezza
        
        # Esegue la simulazione
        while not self.event_queue.is_empty() and event_count < max_events:
            event = self.event_queue.pop()
            event = event[0] if isinstance(event, list) else event
            
            if event_count % 10 == 0:
                print(f"Processando evento {event_count}: {event.serviceName} - {event.eventType}")
            
            if event.handler:
                new_events = event.handler()
                if new_events:
                    for new_event in new_events:
                        # Validate event before adding to queue
                        if new_event and hasattr(new_event, 'timestamp') and new_event.timestamp is not None:
                            self.event_queue.push(new_event)
                        else:
                            print(f"Warning: Skipping invalid event with None timestamp from {event.serviceName}")
            
            event_count += 1
        
        # Finalizza e stampa risultati
        print(f"\nSimulazione completata dopo {event_count} eventi")
        print("Finalizzazione risultati...")
        endBlock.finalize()
        
        # Stampa statistiche dei blocchi
        self.print_block_statistics(instradamento, autenticazione, evasione, 
                                   accettazioneDiretta, inEsame)
    
    def print_block_statistics(self, *blocks):
        """Stampa statistiche per tutti i blocchi passati."""
        print("\n" + "="*50)
        print("STATISTICHE DEI BLOCCHI")
        print("="*50)
        
        for block in blocks:
            print(f"\n{block.name}:")
            print(f"  - Coda attuale: {block.queueLenght}")
            print(f"  - Servizi attivi: {block.working}")
            if hasattr(block, 'multiServiceRate'):
                print(f"  - Capacità massima: {block.multiServiceRate}")
            if hasattr(block, 'rate'):
                print(f"  - Tasso di servizio: {block.rate}")


def main():
    """Funzione principale per eseguire il test."""
    print("Test dei blocchi di simulazione")
    print("="*40)
    
    tester = BlockTester()
    
    # Test con diversi numeri di persone
    test_sizes = [5, 10, 20]
    
    for size in test_sizes:
        print(f"\n{'='*60}")
        print(f"TEST CON {size} PERSONE")
        print(f"{'='*60}")
        
        try:
            tester.test_all_blocks(size)
            print(f"✓ Test con {size} persone completato con successo")
        except Exception as e:
            print(f"✗ Errore nel test con {size} persone: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
