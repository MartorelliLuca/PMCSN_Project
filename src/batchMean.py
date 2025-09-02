from math import sqrt
import json
from desPython import rvms

def read_stats(file_path, n):
    """
    Legge i dati dai file JSON giornalieri.
    Per ogni servizio, crea liste di valori per queue_time, service_time, response_time.
    Se response_time non è presente, viene calcolato come queue_time + service_time.
    Restituisce: dict { "Service:metric": [valori,...] }
    """
    service_data = {}
    with open(file_path, 'r') as f:
        first = True
        for line in f:
            if first:
                first = False
                continue
            day = json.loads(line)
            stats = day.get("stats", {})
            for service_name, service_stats in stats.items():
                queue_values = service_stats['data'].get('queue_time', [])
                service_values = service_stats['data'].get('executing_time', [])
                min_len = min(len(queue_values), len(service_values))
                response_values = [queue_values[i] + service_values[i] for i in range(min_len)]

                metrics_map = {
                    'queue_time': queue_values,
                    'service_time': service_values,
                    'response_time': response_values
                }

                for metric, values in metrics_map.items():
                    key = f"{service_name}:{metric}"
                    if key not in service_data:
                        service_data[key] = []
                    if len(service_data[key]) >= n:
                        continue
                    service_data[key].extend(values[:n - len(service_data[key])])
    return service_data

def computeBatchMeans(data, batch_count):
    """
    Divide i dati in batch_count batch e ritorna le medie dei batch.
    """
    batch_size = len(data) // batch_count
    means = []
    for i in range(batch_count):
        batch = data[i*batch_size:(i+1)*batch_size]
        if not batch:
            continue
        m = sum(batch)/len(batch)
        means.append(m)
    return means

def computeBatchStdev(data, batch_count):
    """
    Divide i dati in batch_count batch e ritorna le deviazioni standard dei batch.
    """
    batch_size = len(data) // batch_count
    stdevs = []
    for i in range(batch_count):
        batch = data[i*batch_size:(i+1)*batch_size]
        if not batch:
            continue
        m = sum(batch)/len(batch)
        s = sqrt(sum((x - m)**2 for x in batch)/len(batch))
        stdevs.append(s)
    return stdevs

def getStudent(k):
    """
    Restituisce il t-critico per un intervallo di confidenza al 95%.
    """
    alpha = 0.05
    return rvms.idfStudent(k - 1, 1 - alpha/2)


# =============================
# Test manuale (solo se eseguito direttamente)
# =============================
if __name__ == "__main__":
    n = 64 * 100

    stats = read_stats('transient_analysis_json/daily_stats.json', n)
    batchesMean = {}
    batchesStdev = {}

    # Calcolo batch means e stdev
    for service, data in stats.items():
        means = computeBatchMeans(data, 64)
        stdevs = computeBatchStdev(data, 64)
        batchesMean[service] = means
        batchesStdev[service] = stdevs

    # Calcolo intervalli di confidenza
    for service, means in batchesMean.items():
        k_eff = len(means)
        if k_eff < 2:
            continue
        mean_sim = sum(means)/k_eff
        var_sim = sum((x - mean_sim)**2 for x in means)/(k_eff - 1)
        se = sqrt(var_sim/k_eff)
        tcrit = getStudent(k_eff)
        ci = (mean_sim - tcrit*se, mean_sim + tcrit*se)
        print(f"\nService: {service}")
        print(f"Media simulata = {mean_sim:.4f}, 95% CI = [{ci[0]:.4f}, {ci[1]:.4f}]")
