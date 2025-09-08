import json
import pandas as pd
from collections import defaultdict

def aggregate_monthly_response_times(daily_stats_file="/home/giulia/Documenti/PM_project/PMCSN_Project/src/transient_analysis_json/daily_stats.json"):
    """
    Legge i daily_stats e calcola i tempi di risposta medi aggregati per mese.
    Restituisce un dict { "Service": { "YYYY-MM": mean_response_time, ... } }
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
            day_str = data.get("date")  # deve esserci nel JSON
            if not day_str:
                continue
            day = pd.to_datetime(day_str)

            for service_name, service_data in stats.items():
                if service_name == "InValutazione":
                    visited = service_data.get("visited", {})
                    queue_time = service_data.get("queue_time", {})
                    execution_time = service_data.get("executing_time", {})

                    if isinstance(visited, dict):  # più code di priorità
                        for priority in visited.keys():
                            full_service_name = f"InValutazione_{priority}"
                            rt = queue_time.get(priority, 0.0) + execution_time.get(priority, 0.0)
                            records.append((full_service_name, day, rt))
                    else:  # versione semplice
                        rt = service_data.get("queue_time", 0.0) + service_data.get("executing_time", 0.0)
                        records.append(("InValutazione", day, rt))
                else:
                    rt = service_data.get("queue_time", 0.0) + service_data.get("executing_time", 0.0)
                    records.append((service_name, day, rt))

    # DataFrame per aggregazione
    df = pd.DataFrame(records, columns=["service", "date", "response_time"])
    df["month"] = df["date"].dt.to_period("M")  # YYYY-MM

    # Media mensile
    monthly = df.groupby(["service", "month"])["response_time"].mean().reset_index()

    # Converto in dict annidato
    result = defaultdict(dict)
    for _, row in monthly.iterrows():
        result[row["service"]][str(row["month"])] = row["response_time"]

    return result


if __name__ == "__main__":
    monthly_stats = aggregate_monthly_response_times()

    for service, months in monthly_stats.items():
        print(f"\n📌 Servizio: {service}")
        for month, avg_rt in months.items():
            print(f"  {month}: {avg_rt:.4f} secondi")
