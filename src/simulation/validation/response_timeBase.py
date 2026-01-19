import json
import pandas as pd
from collections import defaultdict

def aggregate_monthly_response_times(daily_stats_file="/home/giulia/Documenti/PM_project/PMCSN_Project/src/finite_horizon_json_base/daily_stats_rep0.json"):
    """
    Legge i daily_stats e calcola i tempi di risposta medi aggregati per mese,
    pesati sul numero di visite (visited). Restituisce un dict:
    { "Service": { "YYYY-MM": mean_response_time, ... } }
    """
    records = []

    with open(daily_stats_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)

            if data.get("type") != "daily_summary":
                continue

            stats = data.get("stats", {})
            day_str = data.get("date")
            if not day_str:
                continue
            day = pd.to_datetime(day_str)

            # accumuliamo InValutazione per totale
            invalutazione_total_time = 0.0
            invalutazione_total_visits = 0

            for service_name, service_data in stats.items():
                visited = service_data.get("visited", 1)
                queue_time = service_data.get("queue_time", 0.0)
                executing_time = service_data.get("executing_time", 0.0)
                total_time = queue_time + executing_time

                records.append((service_name, day, total_time, visited))

                # se è InValutazione accumulo per TOT
                if service_name == "InValutazione":
                    invalutazione_total_time += total_time
                    invalutazione_total_visits += visited

            # aggiungo il totale InValutazione come servizio separato
            if invalutazione_total_visits > 0:
                records.append(("InValutazione_TOT", day, invalutazione_total_time, invalutazione_total_visits))

    # Creazione DataFrame
    df = pd.DataFrame(records, columns=["service", "date", "total_time", "visited"])
    df["month"] = df["date"].dt.to_period("M")

    # Calcolo media pesata mensile
    monthly_df = (
        df.groupby(["service", "month"])
          .apply(lambda x: x["total_time"].sum() / x["visited"].sum())
          .reset_index(name="response_time")
    )

    # Converto in dict annidato
    result = defaultdict(dict)
    for _, row in monthly_df.iterrows():
        result[row["service"]][str(row["month"])] = row["response_time"]

    return result


if __name__ == "__main__":
    monthly_stats = aggregate_monthly_response_times()

    for service, months in monthly_stats.items():
        print(f"\n📌 Servizio: {service}")
        for month, avg_rt in months.items():
            print(f"  {month}: {avg_rt:.4f} secondi")
