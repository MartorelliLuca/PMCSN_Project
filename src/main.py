import sys
from simulation.SimulationEngine import SimulationEngine as BaseEngine
from simulation.SimulationEngineMigliorativa import SimulationEngine as MigliorativoEngine
from simulation.verification.blocks.SimulationEngine import SimulationEngine as ExponentialEngine 
from simulation.verification.SimulationEnginePriority import SimulationEngine as PriorityEngine



def main():
    print("=== Avvio Simulazione ===\n")

    # Scelta del modello
    print("Seleziona il modello:")
    print("1 - Modello Base")
    print("2 - Modello Migliorativo")
    
    scelta_modello = input("Inserisci scelta: ").strip()

    if scelta_modello == "1":
        engine = BaseEngine()
    elif scelta_modello == "2":
        engine = MigliorativoEngine()
    else:
        print("Scelta non valida. Uscita.")
        sys.exit(1)

    # Scelta del tipo di simulazione
    print("\nSeleziona il tipo di simulazione:")
    print("1 - Simulazione orizzonte finito a tasso variabile Singola Iterazione")
    print("2 - Simulazione orizzonte finito a tasso costante Singola Iterazione")
    print("3 - Verifica Modello Base\n")
    print("4 - Simulazione orizzonte finito a tasso variabile Con Replicazioni")
    print("5 - Simulazione orizzonte finito a tasso costante Con Replicazioni\n")
    print("6 - Simulazione Transitoria")
    print("7 - Verifica Modello Migliorativo\n")
    scelta_simulazione = input("Inserisci scelta: ").strip()

    if scelta_simulazione == "1":
        daily_rates = engine.getArrivalsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale_single_iteration(daily_rates)
    elif scelta_simulazione == "2":
        daily_rates = engine.getArrivalsEqualsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale_single_iteration(daily_rates)
    elif scelta_simulazione == "3":
        engine = ExponentialEngine() 
        daily_rates = engine.getArrivalsRatesToInfinite()
         # Avvio simulazione
        print("\n--- Avvio della simulazione e analisi batch ---\n")
        results = engine.run_and_analyze(
            daily_rates=daily_rates,
            n=64*100,
            batch_count=64,
            theo_json="theo_values.json"
        )
    elif scelta_simulazione == "4":
        daily_rates = engine.getArrivalsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale_with_replication(16, 123456789, daily_rates)
    elif scelta_simulazione == "5":
        daily_rates = engine.getArrivalsEqualsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale_with_replication(7, 123456789, daily_rates)
    elif scelta_simulazione == "6":
        # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.run_transient_analysis(7, 123456789)
    elif scelta_simulazione == "7":
        # Avvio simulazione
        engine = PriorityEngine()
        daily_rates = engine.getArrivalsRatesToInfinite()
         # Avvio simulazione
        print("\n--- Avvio della simulazione e analisi batch ---\n")
        results = engine.run_and_analyze(
            daily_rates=daily_rates,
            n=64*100,
            batch_count=64,
            theo_json="theo_valuesP.json"
        )


    else:
        print("Scelta non valida. Uscita.")
        sys.exit(1)


if __name__ == "__main__":
    main()
