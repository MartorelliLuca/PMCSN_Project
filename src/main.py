import sys
from simulation.SimulationEngine import SimulationEngine as BaseEngine
from simulation.SimulationEngineMigliorativa import SimulationEngine as MigliorativoEngine
from simulation.verification.base.SimulationEngine import SimulationEngineExp as ExponentialEngine 
from simulation.verification.SimulationEnginePriority import SimulationEngine as PriorityEngine



def menu_verifiche():
    """Menu per le verifiche dei modelli."""
    print("\n" + "="*60)
    print("   VERIFICHE MODELLI")
    print("="*60 + "\n")
    
    print("┌" + "─"*58 + "┐")
    print("│" + " "*18 + "SELEZIONA VERIFICA" + " "*21 + "│")
    print("├" + "─"*58 + "┤")
    print("│  1 - Verifica modello base" + " "*30 + "│")
    print("│  2 - Verifica modello migliorativo" + " "*22 + "│")
    print("│  0 - Torna al menu principale" + " "*27 + "│")
    print("└" + "─"*58 + "┘")
    
    scelta = input("\n➤ Inserisci scelta: ").strip()
    
    print("\n" + "="*60)
    
    if scelta == "1":
        engine = ExponentialEngine()
        daily_rates = engine.getArrivalsRates()
        print("▶ Avvio verifica modello base e analisi batch...\n")
        engine.run_and_analyze(
            daily_rates=daily_rates,
            n=64*100,
            batch_count=64,
            theo_json="theo_values.json"
        )
    elif scelta == "2":
        engine = PriorityEngine()
        daily_rates = engine.getArrivalsRatesToInfinite()
        print("▶ Avvio verifica modello migliorativo e analisi batch...\n")
        engine.run_and_analyze(
            daily_rates=daily_rates,
            n=64*100,
            batch_count=64,
            theo_json="theo_valuesP.json"
        )
    elif scelta == "0":
        return
    else:
        print("✗ Scelta non valida.")
        return
    
    print("\n" + "="*60)
    print("   VERIFICA COMPLETATA")
    print("="*60 + "\n")


def main():
    print("\n" + "="*60)
    print("   SISTEMA DI SIMULAZIONE - PMCSN PROJECT")
    print("="*60 + "\n")

    # Scelta del tipo di operazione
    print("┌" + "─"*58 + "┐")
    print("│" + " "*18 + "MENU PRINCIPALE" + " "*25 + "│")
    print("├" + "─"*58 + "┤")
    print("│  1 - Simulazioni" + " "*40 + "│")
    print("│  2 - Verifiche modelli" + " "*33 + "│")
    print("│  0 - Esci" + " "*47 + "│")
    print("└" + "─"*58 + "┘")
    
    scelta_menu = input("\n➤ Inserisci scelta: ").strip()
    
    if scelta_menu == "0":
        print("\n✓ Uscita dal programma.\n")
        sys.exit(0)
    elif scelta_menu == "2":
        menu_verifiche()
        return
    elif scelta_menu != "1":
        print("\n✗ Scelta non valida. Uscita.")
        sys.exit(1)

    # Scelta del modello
    print("\n" + "┌" + "─"*58 + "┐")
    print("│" + " "*20 + "SELEZIONA MODELLO" + " "*21 + "│")
    print("├" + "─"*58 + "┤")
    print("│  1 - Modello Base" + " "*39 + "│")
    print("│  2 - Modello Migliorativo" + " "*31 + "│")
    print("└" + "─"*58 + "┘")
    
    scelta_modello = input("\n➤ Inserisci scelta: ").strip()

    if scelta_modello == "1":
        engine = BaseEngine()
        print("\n✓ Modello Base selezionato")
    elif scelta_modello == "2":
        engine = MigliorativoEngine()
        print("\n✓ Modello Migliorativo selezionato")
    else:
        print("\n✗ Scelta non valida. Uscita.")
        sys.exit(1)

    # Scelta del tipo di simulazione
    print("\n" + "┌" + "─"*58 + "┐")
    print("│" + " "*17 + "SELEZIONA SIMULAZIONE" + " "*20 + "│")
    print("├" + "─"*58 + "┤")
    print("│  1 - Orizzonte finito (10 repliche)" + " "*22 + "│")
    print("│  2 - Orizzonte finito (1 replica)" + " "*23 + "│")
    print("│  3 - Orizzonte finito (tasso variabile, 16 repliche)" + " "*4 + "│")
    print("│  4 - Analisi transitoria (40 repliche)" + " "*18 + "│")
    print("└" + "─"*58 + "┘")
    
    scelta_simulazione = input("\n➤ Inserisci scelta: ").strip()

    print("\n" + "="*60)

    if scelta_simulazione == "1":
        print("▶ Avvio simulazione orizzonte finito...\n")
        engine.run_finito_experiment(n_replicas=10)
        
    elif scelta_simulazione == "2":
        print("▶ Avvio simulazione orizzonte finito (1 replica)...\n")
        engine.run_finito_experiment(n_replicas=1)
        
    elif scelta_simulazione == "3":
        daily_rates = engine.getArrivalsRates()
        print("▶ Avvio simulazione con tasso variabile (16 repliche)...\n")
        engine.normale_with_replication(16, 123456789, daily_rates)
        
    elif scelta_simulazione == "4":
        print("▶ Avvio analisi transitoria (40 repliche)...\n")
        engine.run_transient_analysis(40, 123456789)

    else:
        print("✗ Scelta non valida. Uscita.")
        sys.exit(1)

    print("\n" + "="*60)
    print("   SIMULAZIONE COMPLETATA")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
