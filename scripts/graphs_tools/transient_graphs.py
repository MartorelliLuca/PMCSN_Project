import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict
import pandas as pd

def load_stats_data(filename):
    data = []
    with open(filename, 'r') as f:
        lines = [line for line in f if line.strip()]
        for line in lines:
            data.append(json.loads(line))
    return data

def extract_queue_data(data):
    queue_data = defaultdict(lambda: {
        'queue_times': [],
        'execution_times': [],
        'queue_lengths': [],
        'response_times': []
    })

    for entry in data:
        if entry['type'] != 'daily_summary':
            continue

        stats = entry['stats']
        for queue_name, queue_stats in stats.items():
            if 'data' in queue_stats:
                qt = queue_stats['data']['queue_time']
                et = queue_stats['data']['executing_time']
                rt = [q + e for q, e in zip(qt, et)] if qt and et and len(qt) == len(et) else []

                queue_data[queue_name]['queue_times'].extend(qt)
                queue_data[queue_name]['execution_times'].extend(et)
                queue_data[queue_name]['queue_lengths'].extend(queue_stats['data']['queue_lenght'])
                queue_data[queue_name]['response_times'].extend(rt)

    return queue_data

def apply_log_scale(ax, values, queue_name):
    """Applica scala logaritmica se i valori sono grandi o se è InValutazione"""
    if not values:
        return
    

# 🔑 Mappa hardcoded file → seed
REPLICA_SEEDS = {
    "daily_stats_rep0.json": 123456789,
    "daily_stats_rep1.json": 1049824841,
    "daily_stats_rep2.json": 1343573286,
    "daily_stats_rep3.json": 1455055805,
    "daily_stats_rep4.json": 161222322,
    "daily_stats_rep5.json": 151721053,
    "daily_stats_rep6.json": 752455240,
}

def plot_comparison_chart(queue_name, replica_data, output_dir, replica_seeds):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Confronto tra repliche (tempo medio di attesa)")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Tempo Medio di Attesa (s)")
    means = [(rep, np.mean(times)) for rep, times in replica_data.items() if times]
    means.sort()
    if not means:
        return
    labels, values = zip(*means)
    # Simplified labels without seeds
    bar_labels = [f"Rep {i}" for i in range(len(labels))]
    ax.bar(bar_labels, values, color='skyblue')
    apply_log_scale(ax, values, queue_name)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/confronto_{queue_name.lower()}.jpg", dpi=150, bbox_inches='tight')
    plt.close()

def plot_response_time_averages(queue_name, queue, exec, output_dir, replica_seeds):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Tempi di Risposta (Queue Time + Exec Time)")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Risposta (s)")
    all_vals = []
    replica_count = 0
    for label in sorted(queue.keys()):
        q_times = queue[label]
        e_times = exec[label]
        if len(q_times) < 10 or len(e_times) < 10:
            continue
        exec_moving = pd.Series(e_times).rolling(window=1000, min_periods=1).mean().tolist()
        response_times = [q + e for q, e in zip(q_times, exec_moving)]
        moving_avg = pd.Series(response_times).rolling(window=100, min_periods=1).mean()
        ax.plot(moving_avg, linewidth=0.8, alpha=0.7)  # Remove individual replica labels
        all_vals.extend(response_times)
        replica_count += 1
    if all_vals:
        # Calculate mean using all data
        mean_val = np.mean(all_vals)
        ax.axhline(mean_val, color='red', linestyle='--', label=f"Mean: {mean_val:.2f}", linewidth=1)
    apply_log_scale(ax, all_vals, queue_name)
    ax.grid(True, alpha=0.3)
    ax.legend()  # Only shows the mean line now
    plt.tight_layout()
    plt.savefig(f"{output_dir}/tempi_di_risposta_{queue_name.lower()}.jpg", dpi=150, bbox_inches='tight')
    plt.close()

def plot_aggregated_averages(queue_name, data, output_dir, replica_seeds):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Tempi di Attesa (tutte le repliche)")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Attesa (s)")
    replica_count = 0
    for label in sorted(data.keys()):
        q_times = data[label]
        if len(q_times) < 10:
            continue
        moving_avg = pd.Series(q_times).rolling(window=max(10, len(q_times)//50)).mean()
        ax.plot(moving_avg, alpha=0.7)  # Remove individual replica labels
        replica_count += 1
    
    # Calculate and show overall mean
    all_values = [v for arr in data.values() for v in arr if arr]
    if all_values:
        overall_mean = np.mean(all_values)
        ax.axhline(overall_mean, color='red', linestyle='--', label=f"Mean: {overall_mean:.2f}", linewidth=1)
    
    apply_log_scale(ax, [v for arr in data.values() for v in arr], queue_name)
    ax.grid(True, alpha=0.3)
    ax.legend()  # Only shows the mean line now
    plt.tight_layout()
    plt.savefig(f"{output_dir}/tempi_attesa_{queue_name.lower()}.jpg", dpi=150, bbox_inches='tight')
    plt.close()

def analyze_transient_analysis_directory(transient_dir="transient_analysis_json", output_dir="graphs/transient_avg"):
    if not os.path.exists(transient_dir):
        print(f"Directory {transient_dir}/ non trovata.")
        return

    json_files = [f for f in os.listdir(transient_dir)
                  if f.startswith("daily_stats_rep") and f.endswith(".json")]
    if not json_files:
        print(f"Nessun file daily_stats_rep*.json trovato in {transient_dir}/")
        return

    print(f"\n📊 Analisi transitoria: trovati {len(json_files)} file in {transient_dir}/")

    all_queue_times = defaultdict(lambda: defaultdict(list))
    all_response_times = defaultdict(lambda: defaultdict(list))
    all_exec_times = defaultdict(lambda: defaultdict(list))
    for file in json_files:
        path = os.path.join(transient_dir, file)
        fname = os.path.basename(file)
        print(f"  Caricamento {fname} ...")
        data = load_stats_data(path)
        queue_data = extract_queue_data(data)

        for queue_name, q_data in queue_data.items():
            all_queue_times[queue_name][fname] = q_data['queue_times']
            all_response_times[queue_name][fname] = q_data['response_times']
            all_exec_times[queue_name][fname] = q_data['execution_times']

    os.makedirs(output_dir, exist_ok=True)

    for queue_name in all_queue_times:
        print(f"\n🔍 Analisi per la coda: {queue_name}")
        plot_aggregated_averages(queue_name, all_queue_times[queue_name], output_dir, REPLICA_SEEDS)
        plot_comparison_chart(queue_name, all_queue_times[queue_name], output_dir, REPLICA_SEEDS)
        plot_response_time_averages(queue_name, all_queue_times[queue_name], all_exec_times[queue_name], output_dir, REPLICA_SEEDS)
        
    print(f"\n✅ Analisi completata. Grafici salvati in: {output_dir}/")

if __name__ == "__main__":
    analyze_transient_analysis_directory()
