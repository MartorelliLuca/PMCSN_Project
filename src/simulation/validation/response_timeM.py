import json
import pandas as pd
from collections import defaultdict

def aggregate_monthly_response_times(daily_stats_file):
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
            day = pd.to_datetime(data.get("date"))

            # accumulo totale per InValutazione
            inval_total_time = 0.0
            inval_total_visits = 0

            for service_name, service_data in stats.items():
                visited_data = service_data.get("visited", 1)
                queue_data = service_data.get("queue_time", 0.0)
                exec_data = service_data.get("executing_time", 0.0)

                if isinstance(visited_data, dict):
                    # multi-coda
                    for priority in visited_data:
                        visits = visited_data[priority]
                        total_time = queue_data.get(priority, 0.0) + exec_data.get(priority, 0.0)
                        full_service_name = f"{service_name}_{priority}"
                        records.append((full_service_name, day, total_time, visits))
                        # accumulo totale per TOT
                        inval_total_time += total_time
                        inval_total_visits += visits
                else:
                    total_time = queue_data + exec_data
                    records.append((service_name, day, total_time, visited_data))
                    if service_name == "InValutazione":
                        inval_total_time += total_time
                        inval_total_visits += visited_data

            # aggiungo InValutazione_TOT
            if inval_total_visits > 0:
                records.append(("InValutazione_TOT", day, inval_total_time, inval_total_visits))

    # DataFrame
    df = pd.DataFrame(records, columns=["service", "date", "total_time", "visited"])
    df["month"] = df["date"].dt.to_period("M")

    # media mensile pesata sulle visite
    monthly_df = df.groupby(["service", "month"]).apply(
        lambda x: x["total_time"].sum() / x["visited"].sum()
    ).reset_index(name="response_time")

    # conteggio visite totali mensili
    visits_df = df.groupby(["service", "month"])["visited"].sum().reset_index(name="total_visits")

    # dict annidati
    response_dict = defaultdict(dict)
    visits_dict = defaultdict(dict)

    for _, row in monthly_df.iterrows():
        response_dict[row["service"]][str(row["month"])] = row["response_time"]

    for _, row in visits_df.iterrows():
        visits_dict[row["service"]][str(row["month"])] = row["total_visits"]

    return response_dict, visits_dict


if __name__ == "__main__":
    monthly_stats, monthly_visits = aggregate_monthly_response_times(
        "/home/giulia/Documenti/PM_project/PMCSN_Project/src/finite_horizon_json_base/daily_stats_rep0.json"
    )

    print("\n📌 Tempi medi mensili (secondi):")
    for service, months in monthly_stats.items():
        print(f"\nServizio: {service}")
        for month, avg_rt in months.items():
            print(f"  {month}: {avg_rt:.4f}")

    print("\n📌 Visite totali mensili:")
    for service, months in monthly_visits.items():
        print(f"\nServizio: {service}")
        for month, total_visits in months.items():
            print(f"  {month}: {total_visits}")




def total_response_invalutazione(daily_stats_file):
    """
    Calcola il totale del tempo InValutazione (queue + executing)
    senza dividere per il numero di visite.
    Restituisce dict { "YYYY-MM": tempo_totale }
    """
    total_records = []

    with open(daily_stats_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if data.get("type") != "daily_summary":
                continue
            stats = data.get("stats", {})
            day = pd.to_datetime(data.get("date"))
            month = day.to_period("M")

            inval_total_time = 0.0

            service_data = stats.get("InValutazione")
            if service_data:
                visited_data = service_data.get("visited", 1)
                queue_data = service_data.get("queue_time", 0.0)
                exec_data = service_data.get("executing_time", 0.0)

                if isinstance(visited_data, dict):
                    for priority in visited_data:
                        total_time = queue_data.get(priority, 0.0) + exec_data.get(priority, 0.0)
                        inval_total_time += total_time
                else:
                    inval_total_time += queue_data + exec_data

            total_records.append((month, inval_total_time))

    # somma totale per mese
    df = pd.DataFrame(total_records, columns=["month", "total_time"])
    monthly_total = df.groupby("month")["total_time"].sum().to_dict()

    return monthly_total

# 🔹 Esempio di esecuzione
if __name__ == "__main__":
    file_json = "/home/giulia/Documenti/PM_project/PMCSN_Project/src/finite_horizon_json_base/daily_stats_rep0.json"

    # Media pesata
    monthly_stats, monthly_visits = aggregate_monthly_response_times(file_json)
    print("\n📌 Media mensile pesata (secondi):")
    for service, months in monthly_stats.items():
        print(f"\nServizio: {service}")
        for month, avg_rt in months.items():
            print(f"  {month}: {avg_rt:.4f}")

    # Totale senza pesatura
    monthly_total = total_response_invalutazione(file_json)
    print("\n📌 Totale tempo InValutazione senza pesatura (secondi):")
    for month, total in monthly_total.items():
        print(f"  {month}: {total:.4f}")