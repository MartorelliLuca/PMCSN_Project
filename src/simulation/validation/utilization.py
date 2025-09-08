import json
import os
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt

# --- Configurazione centri (da input.json) ---
centers_config = {
    "inValutazione": {"serversNumber":1, "mean": 3.9447},
    "compilazionePrecompilata": {"serversNumber": 8, "mean": 30},
    "invioDiretto": {"serversNumber": 1, "mean": 3},
    "instradamento": {"serversNumber": 3, "mean": 0.3333},
    "autenticazione": {"serversNumber": 4, "mean": 0.4444}
}

# --- Carica dati giornalieri dal JSON ---
with open("/home/giulia/Documenti/PM_project/PMCSN_Project/conf/dataset_arrivals.json", "r") as f:
    daily_data = json.load(f)["days"]

# --- Calcolo utilizzo giornaliero ---
daily_utilization = defaultdict(list)  # {centro: [(date, utilization_percent), ...]}

for entry in daily_data:
    date = entry["date"]
    lambda_per_sec = entry["lambda_per_sec"]  # arrivi al secondo
    for center, cfg in centers_config.items():
        servers = cfg["serversNumber"]
        mean_service_time = cfg["mean"]  # in secondi
        # utilizzazione U = (λ * S) / m
        utilization = (lambda_per_sec * mean_service_time) / servers
        utilization_percent = min(utilization * 100, 100)
        daily_utilization[center].append((date, utilization_percent))

# --- Raggruppamento mensile ---
monthly_utilization = defaultdict(lambda: defaultdict(list))
# struttura: {centro: {mese: [utilizzazioni,...]}}

for center, values in daily_utilization.items():
    for date_str, util in values:
        month = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")
        monthly_utilization[center][month].append(util)

# --- Calcolo della media mensile ---
monthly_avg_utilization = defaultdict(list)  # {centro: [(mese, media_util)]}
for center, months in monthly_utilization.items():
    for month, utils in sorted(months.items()):
        avg_util = sum(utils) / len(utils)
        monthly_avg_utilization[center].append((month, avg_util))

# --- Stampa mensile tabellare ---
print("\n=== UTILIZZAZIONE MENSILE DEI CENTRI (media %) ===\n")
for center, values in monthly_avg_utilization.items():
    print(f"\n📌 Centro: {center} (servers: {centers_config[center]['serversNumber']}, mean: {centers_config[center]['mean']}s)")
    print("Mese      | Utilizzazione media")
    print("-" * 35)
    for month, avg_util in values:
        # stampo solo il nome del mese
        month_name = datetime.strptime(month, "%Y-%m").strftime("%B")
        print(f"{month_name:9} | {avg_util:6.2f}%")

# --- Salvataggio grafici in una cartella ---
output_dir = "/home/giulia/Documenti/PM_project/PMCSN_Project/src/graphs/utilization"
os.makedirs(output_dir, exist_ok=True)

# --- Grafici mensili raggruppati in un'unica figura ---
n_centers = len(monthly_avg_utilization)
ncols = 2
nrows = (n_centers + ncols - 1) // ncols

fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(14, 3 * nrows))
axes = axes.flatten()

for idx, (center, values) in enumerate(monthly_avg_utilization.items()):
    # converto i mesi in datetime e creo etichette con solo il nome del mese
    months_dt = [datetime.strptime(m, "%Y-%m") for m, _ in values]
    utils = [u for _, u in values]
    month_labels = [m.strftime("%B") for m in months_dt]

    ax = axes[idx]
    ax.plot(month_labels, utils, marker='o', linestyle='-', color='teal')
    ax.set_title(center, fontsize=12, fontweight='bold')
    ax.set_xlabel("Mese")
    ax.set_ylabel("Utilizzazione (%)")
    ax.set_xticklabels(month_labels, rotation=45, ha="right")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)

# Rimuovo eventuali subplot vuoti
for j in range(idx + 1, len(axes)):
    fig.delaxes(axes[j])

plt.suptitle("Utilizzazione Media Mensile per Centro", fontsize=16, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.96])

# --- Salvo e mostro ---
output_path = os.path.join(output_dir, "utilizzazione_mensile_centri.png")
plt.savefig(output_path, dpi=300)
plt.show()
plt.close(fig)

print(f"\n✅ Grafico salvato in: {output_path}")
