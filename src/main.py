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
    print("1 - Simulazione Giornaliera")
    print("2 - Simulazione Transitoria")
    scelta_simulazione = input("Inserisci scelta (1 o 2): ").strip()

    if scelta_simulazione == "1":
        daily_rates = engine.getArrivalsRates()
         # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.normale(daily_rates)
    elif scelta_simulazione == "2":
        # Avvio simulazione
        print("\n--- Avvio della simulazione ---\n")
        engine.run_transient_analysis(n_replicas=10, seed_base=1)

    else:
        print("Scelta non valida. Uscita.")
        sys.exit(1)


if __name__ == "__main__":
    main()
