import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

path = ("/Users/giuliaboccuccia/Documents/PMCSN/PMCSN_Project/src/finite_horizon_json_migliorativo/daily_stats_rep0.json"
    #"/home/giulia/Documenti/PM_project/PMCSN_Project/src/finite_horizon_json_migliorativo/daily_stats_rep0.json"
    #"/Users/giuliaboccuccia/Documents/PMCSN/PMCSN_Project/src/finite_horizon_json_migliorativo/daily_stats_rep0.json"
)

# ======================================================
# COSTANTI
# ======================================================
SECONDS_PER_DAY = 24 * 3600

SERVERS = {
    "CompilazionePrecompilata": 8,
    "InValutazione": 11200,
    "InvioDiretto": 3
}

# ======================================================
# PARSING JSON
# ======================================================
rows_centers = []
rows_classes = []

with open(path) as f:
    for line in f:
        obj = json.loads(line)
        if obj["type"] != "daily_summary":
            continue

        date = datetime.fromisoformat(obj["date"])

        for center, s in obj["stats"].items():

            # =========================
            # SIZE-BASED CENTER
            # =========================
            if isinstance(s["visited"], dict):

                visited_tot = sum(s["visited"].values())
                queue_tot = sum(s["queue_time"].values())
                exec_tot = sum(s["executing_time"].values())

                rows_centers.append({
                    "date": date,
                    "center": center,
                    "visited": visited_tot,
                    "queue_time": queue_tot,
                    "executing_time": exec_tot
                })

                for cls in s["visited"]:
                    rows_classes.append({
                        "date": date,
                        "center": center,
                        "class": cls,
                        "visited": s["visited"][cls],
                        "queue_time": s["queue_time"][cls],
                        "executing_time": s["executing_time"][cls]
                    })

            # =========================
            # NORMAL CENTER
            # =========================
            else:
                rows_centers.append({
                    "date": date,
                    "center": center,
                    "visited": s["visited"],
                    "queue_time": s["queue_time"],
                    "executing_time": s["executing_time"]
                })

# ======================================================
# DATAFRAMES
# ======================================================
df_centers = pd.DataFrame(rows_centers).sort_values("date")
df_classes = pd.DataFrame(rows_classes).sort_values("date")

# ======================================================
# METRICHE CENTRI
# ======================================================
df_centers["utilization"] = (
    df_centers["executing_time"]
    / (df_centers["center"].map(SERVERS) * SECONDS_PER_DAY)
)

df_centers["Wq"] = df_centers["queue_time"] / df_centers["visited"]
df_centers["R"] = (
    df_centers["queue_time"] + df_centers["executing_time"]
) / df_centers["visited"]

# ======================================================
# METRICHE CLASSI (NO UTILIZZAZIONE)
# ======================================================
df_classes["Wq"] = df_classes["queue_time"] / df_classes["visited"]
df_classes["R"] = (
    df_classes["queue_time"] + df_classes["executing_time"]
) / df_classes["visited"]

# ======================================================
# PLOT 1 — UTILIZZAZIONE CENTRI
# ======================================================
plt.figure()
for center in df_centers["center"].unique():
    sub = df_centers[df_centers["center"] == center]
    plt.plot(sub["date"], sub["utilization"], label=center)

plt.axhline(1.0, linestyle="--")
plt.title("Utilizzazione giornaliera – centri")
plt.xlabel("Tempo")
plt.ylabel("ρ")
plt.legend()
plt.tight_layout()
plt.show()

# ======================================================
# PLOT 2 — Wq CENTRI
# ======================================================
plt.figure()
for center in df_centers["center"].unique():
    sub = df_centers[df_centers["center"] == center]
    plt.plot(sub["date"], sub["Wq"], label=center)

plt.yscale("log")
plt.title("Tempo medio in coda (Wq) – centri")
plt.xlabel("Tempo")
plt.ylabel("Secondi")
plt.legend()
plt.tight_layout()
plt.show()

# ======================================================
# PLOT 3 — R CENTRI
# ======================================================
plt.figure()
for center in df_centers["center"].unique():
    sub = df_centers[df_centers["center"] == center]
    plt.plot(sub["date"], sub["R"], label=center)

plt.yscale("log")
plt.title("Tempo medio di risposta (R) – centri")
plt.xlabel("Tempo")
plt.ylabel("Secondi")
plt.legend()
plt.tight_layout()
plt.show()

# ======================================================
# PLOT 4 — Wq SIZE-BASED (InValutazione)
# ======================================================
plt.figure()
for cls in df_classes["class"].unique():
    sub = df_classes[df_classes["class"] == cls]
    plt.plot(sub["date"], sub["Wq"], label=cls)

plt.yscale("log")
plt.title("Valutazione Pratiche – Tempo medio in coda per classe")
plt.xlabel("Tempo")
plt.ylabel("Secondi")
plt.legend()
plt.tight_layout()
plt.show()

# ======================================================
# PLOT 5 — R SIZE-BASED (InValutazione)
# ======================================================
plt.figure()
for cls in df_classes["class"].unique():
    sub = df_classes[df_classes["class"] == cls]
    plt.plot(sub["date"], sub["R"], label=cls)

plt.yscale("log")
plt.title("Valutazione Pratiche – Tempo medio di risposta per classe")
plt.xlabel("Tempo")
plt.ylabel("Secondi")
plt.legend()
plt.tight_layout()
plt.show()

# ======================================================
# CHECK RAPIDO
# ======================================================
print("\n--- CENTERS ---")
print(df_centers.head())

print("\n--- CLASSES ---")
print(df_classes.head())
