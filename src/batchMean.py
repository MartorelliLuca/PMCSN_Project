from math import sqrt
import json
import matplotlib.pyplot as plt
import numpy as np
import os
from desPython import rvms



"""
IMPORTANTE: autocorr_stats implementa la funzionalita di acs.py di DesPython.

NOTE: Vecchia versioene, utilizzare batchMeanPriority.py
"""



"""def read_stats(file_path, n):

    Legge i dati dai file JSON giornalieri.
    Per ogni servizio, crea liste di valori per queue_time, service_time, response_time.
    Se response_time non è presente, viene calcolato come queue_time + service_time.
    Restituisce: dict { "Service:metric": [valori,...] }
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
    return service_data"""
def read_stats(file_path, n):
    """
    Legge i dati dai file JSON giornalieri come quello che hai mostrato.
    Per ogni servizio, crea liste di valori per queue_time, service_time, response_time.
    Restituisce: dict { "Service:metric": [valori,...] }
    """
    import json

    service_data = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            day = json.loads(line)  # carica il JSON della giornata
            stats = day.get("stats", {})
            for service_name, service_stats in stats.items():
                queue_values = service_stats["data"].get("queue_time", [])
                exec_values = service_stats["data"].get("executing_time", [])
                min_len = min(len(queue_values), len(exec_values))
                response_values = [queue_values[i] + exec_values[i] for i in range(min_len)]

                metrics_map = {
                    "queue_time": queue_values,
                    "service_time": exec_values,
                    "response_time": response_values
                }

                for metric, values in metrics_map.items():
                    key = f"{service_name}:{metric}"
                    if key not in service_data:
                        service_data[key] = []
                    # Limita a n valori
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




def autocorr_stats(arr, k):
  """
  arr: list of floats
  k: maximum lag
  Returns: (autocorr_1, mean, stdev)
  """
  SIZE = k + 1
  n = len(arr)
  if n <= k:
    raise ValueError("Number of data points must be greater than k.")
  hold = arr[:SIZE]
  cosum = [0.0 for _ in range(SIZE)]
  sum_x = sum(hold)
  p = 0
  i = SIZE
  # Main loop
  while i < n:
    for j in range(SIZE):
      cosum[j] += hold[p] * hold[(p + j) % SIZE]
    x = arr[i]
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
  stdev = sqrt(cosum[0])
  autocorr_1 = cosum[1] / cosum[0] if cosum[0] != 0 else 0.0
  return autocorr_1, mean, stdev

# =============================
# Test manuale (solo se eseguito direttamente)
# =============================
if __name__ == "__main__":
    
    def read_daily_stats(filename):
        """
        Reads a json-lines file, skips the first line, and returns a list of dicts for each daily summary.
        """
        rows = []
        with open(filename, 'r') as f:
            first = True
            for line in f:
                if first:
                    first = False
                    continue  # skip metadata
                if line.strip():
                    rows.append(json.loads(line))
        return rows
    
    stats = read_daily_stats('transient_analysis_json/daily_statsaaa.json')
    centers=["Autenticazione","Instradamento","CompilazionePrecompilata","InvioDiretto","InValutazione"]
    centersData={center:{
    "queue_time": [],
    "executing_time": [],
    } for center in centers}

    for row in stats:
        # Check if row has "stats" key
        if "stats" not in row:
            print("Warning: No 'stats' key in this row, skipping...")
            continue
            
        row_stats = row["stats"]
        # Check if all centers exist in stats
        all_centers_present = all(center in row_stats.keys() for center in centers)
        if(not all_centers_present):
            break
        
        for center in centers:
            if all_centers_present:  # Only process if center exists
                centersData[center]["queue_time"].append(row_stats[center]["queue_time"])
                centersData[center]["executing_time"].append(row_stats[center]["executing_time"])
            else:
                print(f"Warning: {center} not found in stats")

    # Debug: Check data sizes
    for center in centers:
        print(f"{center}: {len(centersData[center]['queue_time'])} data points")

    # Find optimal k for all services using powers of 2 from 32 to 128
    k_powers = [32, 64, 128]
    best_k = None
    best_score = float('inf')  # Lower is better
    k_results = {}
    
    print(f"\nTesting k values: {k_powers}")
    
    for k in k_powers:
        k_score = 0
        services_with_valid_k = 0
        k_results[k] = {}
        
        for service in centers:
            queue_times = centersData[service]["queue_time"]
            
            # Skip if no data available
            if len(queue_times) == 0:
                continue
                
            max_k = len(queue_times)
            
            # Check if we have enough data for this k
            if max_k < k:
                print(f"  {service}: Not enough data for k={k} (only {max_k} points)")
                k_results[k][service] = None
                continue
                
            # Calculate batch size
            b = max_k // k  # Batch size
            if b == 0:
                k_results[k][service] = None
                continue
                
            new_n = k * b
            temp_queue_times = queue_times[:new_n]
            
            # Calculate batch means for current k
            batch_queue_means = []
            
            for i in range(k):
                start = i * b
                end = (i + 1) * b
                qt_batch = temp_queue_times[start:end]
                
                if len(qt_batch) > 0:
                    batch_queue_means.append(sum(qt_batch) / len(qt_batch))
            
            # Skip if we don't have enough batches
            if len(batch_queue_means) < 2:
                k_results[k][service] = None
                continue
                
            try:
                # Calculate autocorrelation for queue times
                correlation_q, mean_q, std_q = autocorr_stats(batch_queue_means, min(64, len(batch_queue_means)-1))
                
                k_results[k][service] = {
                    'correlation': correlation_q,
                    'mean': mean_q,
                    'std': std_q,
                    'batch_means': batch_queue_means,
                    'batch_size': b,
                    'original_size': len(queue_times),
                    'used_size': new_n
                }
                
                # Add squared correlation to score (we want low correlations)
                k_score += correlation_q ** 2
                services_with_valid_k += 1
                
                print(f"  {service}: k={k}, |correlation|={abs(correlation_q):.4f}, batch_size={b}")
                
            except Exception as e:
                print(f"  {service}: Failed for k={k}: {e}")
                k_results[k][service] = None
                continue
        
        if services_with_valid_k > 0:
            avg_score = k_score / services_with_valid_k
            print(f"k={k}: Average squared correlation = {avg_score:.6f} ({services_with_valid_k} services)")
            
            if avg_score < best_score:
                best_score = avg_score
                best_k = k
        else:
            print(f"k={k}: No valid services")
    
    if best_k is None:
        print("ERROR: Could not find any valid k value for any service!")
        exit(1)
    
    print(f"\nSelected optimal k={best_k} with average squared correlation = {best_score:.6f}")
    
    # Apply the best k to all services
    for service in centers:
        if best_k in k_results and service in k_results[best_k] and k_results[best_k][service] is not None:
            result = k_results[best_k][service]
            centersData[service]["queue_time_analysis"] = {
                'correlation': result['correlation'],
                'mean': result['mean'],
                'std': result['std'],
                'k': best_k,
                'batch_means': result['batch_means'],
                'batch_size': result['batch_size'],
                'original_size': result['original_size'],
                'used_size': result['used_size']
            }
            print(f"{service}: k={best_k}, |correlation|={abs(result['correlation']):.4f}, batch_size={result['batch_size']}")
        else:
            print(f"Warning: {service} has no valid analysis for k={best_k}")
            centersData[service]["queue_time_analysis"] = None



    # Calcolo intervalli di confidenza (only for queue times)
    print("\n" + "="*60)
    print("CONFIDENCE INTERVALS (Queue Times Only)")
    print("="*60)
    
    for service in centers:
        # Skip if service doesn't have the required data
        if "queue_time_analysis" not in centersData[service] or centersData[service]["queue_time_analysis"] is None:
            print(f"Warning: No analysis data for {service}, skipping confidence intervals...")
            continue
            
        analysis = centersData[service]["queue_time_analysis"]
        correlation = analysis['correlation']
        mean_val = analysis['mean']
        std_val = analysis['std']
        k = analysis['k']
        student = getStudent(k)
        
        se = std_val / sqrt(k - 1)
        ci = (mean_val - student * se, mean_val + student * se)
        
        print(f"{service}: mean={mean_val:.6f}, std={std_val:.6f}, 95% CI=[{ci[0]:.6f}, {ci[1]:.6f}], autocorr={correlation:.4f}")
    
    print("="*60)

    # Create directory for batch mean graphs
    output_dir = "batchMeanGraphs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot batch means for each service (only queue times)
    for service in centers:
        # Skip if service doesn't have the required data
        if "queue_time_analysis" not in centersData[service] or centersData[service]["queue_time_analysis"] is None:
            print(f"Warning: No batch data for {service}, skipping plots...")
            continue
            
        analysis = centersData[service]["queue_time_analysis"]
        batch_queue_means = analysis["batch_means"]
        k = analysis["k"]
        correlation = analysis['correlation']
        mean_val = analysis['mean']
        std_val = analysis['std']
        student = getStudent(k)
        
        # Calculate confidence interval
        se = std_val / sqrt(k - 1)
        ci = (mean_val - student * se, mean_val + student * se)
        
        # Create single plot for queue times only
        fig, ax = plt.subplots(1, 1, figsize=(12, 6))
        fig.suptitle(f'{service} - Queue Time Batch Means (k={k})', fontsize=14, fontweight='bold')
        
        # Queue Time plot
        ax.plot(range(1, k+1), batch_queue_means, 'bo-', markersize=6, linewidth=2, label='Batch Means')
        ax.axhline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.4f}')
        ax.axhline(ci[0], color='orange', linestyle=':', alpha=0.7, label=f'95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]')
        ax.axhline(ci[1], color='orange', linestyle=':', alpha=0.7)
        ax.set_title(f'Queue Time')
        ax.set_xlabel('Batch Number')
        ax.set_ylabel('Queue Time (s)')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{service}_batch_means.jpg", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Saved batch means plot for {service} in {output_dir}/{service}_batch_means.jpg")
    
    # Save summary statistics to a text file (only queue times)
    summary_file = f"{output_dir}/batch_means_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("BATCH MEANS ANALYSIS SUMMARY - QUEUE TIMES ONLY\n")
        f.write("=" * 60 + "\n")
        f.write(f"Selected k value: {best_k} (optimal for all services)\n")
        f.write(f"Average squared autocorrelation: {best_score:.6f}\n")
        f.write("=" * 60 + "\n\n")
        
        for service in centers:
            if "queue_time_analysis" not in centersData[service] or centersData[service]["queue_time_analysis"] is None:
                f.write(f"{service}: No analysis data available\n\n")
                continue
                
            analysis = centersData[service]["queue_time_analysis"]
            correlation = analysis['correlation']
            mean_val = analysis['mean']
            std_val = analysis['std']
            k = analysis['k']
            batch_size = analysis['batch_size']
            original_size = analysis['original_size']
            used_size = analysis['used_size']
            student = getStudent(k)
            
            # Calculate confidence interval
            se = std_val / sqrt(k - 1)
            ci = (mean_val - student * se, mean_val + student * se)
            
            f.write(f"{service}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Data Set Information:\n")
            f.write(f"  Original data size: {original_size} samples\n")
            f.write(f"  Used data size: {used_size} samples\n")
            f.write(f"  Number of batches (k): {k}\n")
            f.write(f"  Batch size (b): {batch_size} samples per batch\n\n")
            
            f.write(f"Queue Time Analysis:\n")
            f.write(f"  Mean: {mean_val:.8f} seconds\n")
            f.write(f"  Standard Deviation: {std_val:.8f}\n")
            f.write(f"  Standard Error: {se:.8f}\n")
            f.write(f"  95% Confidence Interval: [{ci[0]:.8f}, {ci[1]:.8f}]\n")
            f.write(f"  Autocorrelation (lag-1): {correlation:.6f}\n")
            f.write(f"  |Autocorrelation|: {abs(correlation):.6f}\n\n")
            f.write("=" * 60 + "\n\n")
    
    print(f"✅ Saved summary statistics to {summary_file}")
    print(f"📊 Batch means analysis completed! Used k={best_k} for all services.")
    print(f"📂 Check {output_dir}/ for all results.")                                                                                    
        
        
