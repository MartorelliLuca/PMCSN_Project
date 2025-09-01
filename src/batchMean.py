from math import sqrt
import json
from desPython import rvms


def read_stats(file_path, n):
    """
    For each service, create a list of arrays, each with n queue_time values,
    reading across days and starting a new batch only when n is reached.
    Returns: dict {service_name: [ [queue_time, ...], ... ] }
    """
    service_data = {}
    with open(file_path, 'r') as f:
        first = True
        for line in f:
            if first:
                first = False
                continue  # skip metadata
            day = json.loads(line)
            stats = day.get("stats", {})
            for service_name, service_stats in stats.items():
                # For each metric (queue_time, executing_time)
                for metric in ['queue_time', 'executing_time']:
                    key = f"{service_name}:{metric}"
                    if key not in service_data:
                        service_data[key] = []
                    if len(service_data[key]) >= n:
                        continue
                    service_data[key].extend(service_stats['data'][metric])
                    if len(service_data[key]) > n:
                        service_data[key] = service_data[key][:n]
    return service_data


def autocorrelation_stats(k, data):
    """
    Computes mean, stdev, and autocorrelation coefficients up to lag k for a list of floats.
    Returns mean and stdev.
    """
    SIZE = k + 1
    n = len(data)
    if n <= k:
        print("Error: Number of data points must be greater than k.")
        return

    hold = data[:SIZE]
    cosum = [0.0 for _ in range(SIZE)]
    sum_x = sum(hold)
    p = 0
    i = SIZE

    # Main loop
    while i < n:
        for j in range(SIZE):
            cosum[j] += hold[p] * hold[(p + j) % SIZE]
        x = data[i]
        sum_x += x
        hold[p] = x
        p = (p + 1) % SIZE
        i += 1

    # Flush the circular buffer
    for _ in range(SIZE):
        for j in range(SIZE):
            cosum[j] += hold[p] * hold[(p + j) % SIZE]
        hold[p] = 0.0
        p = (p + 1) % SIZE

    mean = sum_x / n
    for j in range(SIZE):
        cosum[j] = (cosum[j] / (n - j)) - (mean * mean)

    if cosum[0] == 0:
        return mean, sqrt(cosum[0])

    return mean, sqrt(cosum[0])


def computeMeanAndStdev(data, k):
    """
    Splits data into k batches, computes mean and stddev for each batch.
    Returns two lists: means, stddevs (length k)
    """
    batch_size = len(data) // k
    means = []
    stddevs = []
    for i in range(k):
        batch = data[i * batch_size:(i + 1) * batch_size]
        if not batch:
            continue
        m = sum(batch) / len(batch)
        s = sqrt(sum((x - m) ** 2 for x in batch) / len(batch))
        means.append(m)
        stddevs.append(s)
    return means, stddevs


def getStudent(k):
    alpha = 0.05
    val = rvms.idfStudent(k - 1, 1 - alpha / 2)
    return val


# =============================
# Test manuale (solo se eseguito direttamente)
# =============================
if __name__ == "__main__":
    n = 64 * 100  # oppure 143*50

    stats = read_stats('transient_analysis_json/daily_stats.json', n)
    batchesMean = {}
    batchesStdev = {}

    # calculate batch means and stdevs
    for service, data in stats.items():
        mean, std = computeMeanAndStdev(data, 64)
        batchesMean[service] = mean
        batchesStdev[service] = std

    # calculate autocorrelation on batch means and confidence interval
    for service, data in batchesMean.items():
        print(f"\nService: {service}")
        mean, stddev = autocorrelation_stats(20, data)
        student = getStudent(64)
        print(f"95% confidence interval for the mean: {mean}+-{student * (stddev) / sqrt(len(data)):.2f}")
