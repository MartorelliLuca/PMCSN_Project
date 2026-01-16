import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# =========================
# LOAD REAL JSON-LINES FILE
# =========================
# 👉 Cambia solo questo path con il tuo CSV reale
path = "/home/giulia/Documenti/PM_project/PMCSN_Project/src/finite_horizon_json_base/daily_stats_rep0.json"

rows = []
with open(path) as f:
    for line in f:
        obj = json.loads(line)
        if obj["type"] != "daily_summary":
            continue

        date = datetime.fromisoformat(obj["date"])
        for center, s in obj["stats"].items():
            rows.append({
                "date": date,
                "center": center,
                "visited": s["visited"],
                "queue_time": s["queue_time"],
                "executing_time": s["executing_time"]
            })

df = pd.DataFrame(rows).sort_values("date")

# =========================
# PARAMETERS
# =========================
SECONDS_PER_DAY = 24 * 3600
SERVERS = {
    "CompilazionePrecompilata": 8,
    "InValutazione": 11200,
    "InvioDiretto": 3
}

# =========================
# METRICS (DAILY / WINDOWED)
# =========================
df["utilization"] = df.apply(
    lambda r: r["executing_time"] / (SERVERS[r["center"]] * SECONDS_PER_DAY),
    axis=1
)

df["Wq"] = df["queue_time"] / df["visited"]
df["R"] = (df["queue_time"] + df["executing_time"]) / df["visited"]

# =========================
# 1️⃣ DEFINITIVE UTILIZATION PLOT
# =========================
plt.figure()
for center in df["center"].unique():
    sub = df[df["center"] == center]
    plt.plot(sub["date"], sub["utilization"], label=center)

plt.axhline(1.0, linestyle="--")
plt.title("Utilizzazione giornaliera – confronto tra centri")
plt.xlabel("Tempo")
plt.ylabel("Utilizzazione ρ")
plt.legend()
plt.tight_layout()
plt.show()

# =========================
# 2️⃣ DEFINITIVE QUEUE TIME PLOT
# =========================
plt.figure()
for center in df["center"].unique():
    sub = df[df["center"] == center]
    plt.plot(sub["date"], sub["Wq"], label=center)

plt.yscale("log")
plt.title("Tempo medio in coda (Wq) – scala log")
plt.xlabel("Tempo")
plt.ylabel("Secondi")
plt.legend()
plt.tight_layout()
plt.show()

# =========================
# 3️⃣ DEFINITIVE RESPONSE TIME PLOT
# =========================
plt.figure()
for center in df["center"].unique():
    sub = df[df["center"] == center]
    plt.plot(sub["date"], sub["R"], label=center)

plt.yscale("log")
plt.title("Tempo medio di risposta (R) – scala log")
plt.xlabel("Tempo")
plt.ylabel("Secondi")
plt.legend()
plt.tight_layout()
plt.show()

df.head()
