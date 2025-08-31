import sys
from simulation.SimulationEngine import SimulationEngine as BaseEngine
from simulation.SimulationEngineMigliorativa import SimulationEngine as MigliorativoEngine


def main():
    print("=== Avvio Simulazione ===\n")

    # Scelta del modello
    print("Seleziona il modello:")
    print("1 - Modello Base")
    print("2 - Modello Migliorativo")
    scelta_modello = input("Inserisci scelta (1 o 2): ").strip()

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
    print("2 - Simulazione orizzonte finito a tasso costante Singola Iterazione\n")
    print("3 - Simulazione orizzonte finito a tasso variabile Con Replicazioni")
    print("4 - Simulazione orizzonte finito a tasso costante Con Replicazioni\n")
    print("5 - Simulazione Transitoria")
    scelta_simulazione = input("Inserisci scelta (1, 2 o 3): ").strip()

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
        daily_rates = engine.getArrivalsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale_with_constant_replication(daily_rates)
    elif scelta_simulazione == "4":
        daily_rates = engine.getArrivalsEqualsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale_with_replication(daily_rates)
    elif scelta_simulazione == "5":
        # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.run_transient_analysis(n_replicas=10, seed_base=123456789)

    else:
        print("Scelta non valida. Uscita.")
        sys.exit(1)


if __name__ == "__main__":
    main()
