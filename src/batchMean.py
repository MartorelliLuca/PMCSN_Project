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
                if service_name not in service_data:
                    service_data[service_name] = []
                # Extend the service's queue_time list
                if  len(service_data[service_name]) >= n :
                    continue
                service_data[service_name].extend(service_stats['data']['queue_time'])
                if len(service_data[service_name]) > n:
                    service_data[service_name] = service_data[service_name][:n]
            


    
    return service_data



def autocorrelation_stats(k, data):
    """
    Computes mean, stdev, and autocorrelation coefficients up to lag k for a list of floats.
    Prints the results.
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

    print(f"for {n} data points")
    print(f"the mean is ... {mean:8.2f}")
    print(f"the stdev is .. {sqrt(cosum[0]):8.2f}\n")
    print("  j (lag)   r[j] (autocorrelation)\n")
    if cosum[0] == 0:
        print("All data points are zero; autocorrelation is undefined.")
        return  mean,sqrt(cosum[0])
    for j in range(1, 2):
        print(f"{j:3d}  {cosum[j] / cosum[0]:11.3f}")
    return mean,sqrt(cosum[0])



def getStudent(k):
    alpha=0.05
    val=rvms.idfStudent(k-1,1-alpha/2)
    return val

stats=read_stats('daily_stats.json', 5000)
print(f"Found {len(stats)} services with data.")
#print(stats)
for service, data in stats.items():
    print(f"\nService: {service}")
    mean,stddev=autocorrelation_stats(64, data)
    student=getStudent(64)
    print(f"95% confidence interval for the mean: {mean}+-{  student * (stddev )/sqrt(len(data)):.2f}")