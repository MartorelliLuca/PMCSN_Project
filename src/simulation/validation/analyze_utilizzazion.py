import os
import matplotlib.pyplot as plt

# --- Valori medi calcolati o stimati dal SimulationEngine ---
# λ medio (arrivi/sec) e tempo medio di servizio E(S) in secondi
frequenze = {
    "Diretta": 0.037246,
    "Pesante": 0.029198,
    "Leggera": 0.101847
}

tempi_medi_servizio = {
    "Diretta": 3.9492,
    "Pesante": 9.8514,
    "Leggera": 2.2389
}

servers_number = 1  # numero di server del blocco InValutazione

# --- Calcolo utilizzo medio per server ---
utilization_per_server = {}

for q in frequenze.keys():
    utilization_per_server[q] = (frequenze[q] * tempi_medi_servizio[q]) / servers_number

# Utilizzo totale
utilization_per_server["Totale"] = sum(utilization_per_server[q] for q in frequenze.keys())

# --- Stampa risultati ---
print("\n=== Utilizzazione media per server (InValutazione) ===")
for q in list(frequenze.keys()) + ["Totale"]:
    print(f"{q:8}: {utilization_per_server[q]*100:.2f}%")

# --- Grafico orizzontale leggibile ---
output_dir = "./graphs"
os.makedirs(output_dir, exist_ok=True)

labels = list(utilization_per_server.keys())
values = [utilization_per_server[k]*100 for k in labels]
colors = ['skyblue', 'lightgreen', 'salmon', 'orange']

plt.figure(figsize=(10,6))
bars = plt.barh(labels, values, color=colors)

# Aggiungi valori accanto alle barre
for bar in bars:
    plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
             f"{bar.get_width():.1f}%", va='center', fontsize=10)

plt.xlim(0, 100)
plt.xlabel("Utilizzazione media (%)")
plt.title("Utilizzazione media per server - InValutazione", fontsize=14, fontweight='bold')
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()

output_path = os.path.join(output_dir, "invalutazione_utilization_direct.png")
plt.savefig(output_path, dpi=300)
plt.show()
plt.close()

print(f"\n✅ Grafico salvato in: {output_path}")
