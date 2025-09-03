import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict
import pandas as pd

def load_stats_data(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
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
    vmax = max(values)
    if queue_name == "InValutazione":
        ax.set_ylim(0, 300000)

def plot_aggregated_averages(queue_name, data, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Media Mobile Tempi di Attesa (tutte le repliche)")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Attesa (s)")
    for label, q_times in data.items():
        if len(q_times) < 10:
            continue
        moving_avg = pd.Series(q_times).rolling(window=max(10, len(q_times)//50)).mean()
        ax.plot(moving_avg, label=label)
    apply_log_scale(ax, [v for arr in data.values() for v in arr], queue_name)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{output_dir}/media_mobile_{queue_name.lower()}.png", dpi=300)
    plt.close()

def plot_comparison_chart(queue_name, replica_data, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Confronto tra repliche (tempo medio di attesa)")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Tempo Medio di Attesa (s)")
    means = [(rep, np.mean(times)) for rep, times in replica_data.items() if times]
    means.sort()
    if not means:
        return
    labels, values = zip(*means)
    ax.bar(labels, values, color='skyblue')
    apply_log_scale(ax, values, queue_name)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/confronto_{queue_name.lower()}.png", dpi=300)
    plt.close()

def plot_response_time_averages(queue_name, data, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Media Mobile Tempi di Risposta (tutte le repliche)")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Risposta (s)")
    ax.set_yscale('log')
    all_vals = []
    for label, r_times in data.items():
        if len(r_times) < 10:
            continue
        moving_avg = pd.Series(r_times).rolling(window=1200).mean()
        ax.plot(moving_avg, label=label)
        all_vals.extend(r_times)
    if all_vals:
        mean_val = np.mean(all_vals)
        ax.axhline(mean_val, color='red', linestyle='--', label=f"Mean: {mean_val:.2f}")
    apply_log_scale(ax, all_vals, queue_name)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{output_dir}/risposta_media_mobile_{queue_name.lower()}.png", dpi=300)
    plt.close()

def plot_response_times(queue_name, data, output_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{queue_name} - Tempo di Risposta (Attesa + 66000s)")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Risposta (s)")
    all_vals = []
    for label, q_times in data.items():
        if len(q_times) < 10:
            continue
        response_times = [qt + 66000 for qt in q_times]
        moving_avg = pd.Series(response_times).rolling(window=max(10, len(response_times)//50)).mean()
        ax.plot(moving_avg, label=label)
        all_vals.extend(response_times)
    apply_log_scale(ax, all_vals, queue_name)
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{output_dir}/response_time_{queue_name.lower()}.png", dpi=300)
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

    for file in json_files:
        path = os.path.join(transient_dir, file)
        print(f"  Caricamento {file} ...")
        data = load_stats_data(path)
        queue_data = extract_queue_data(data)

        for queue_name, q_data in queue_data.items():
            all_queue_times[queue_name][file] = q_data['queue_times']
            all_response_times[queue_name][file] = q_data['response_times']

    os.makedirs(output_dir, exist_ok=True)

    for queue_name in all_queue_times:
        print(f"\n🔍 Analisi per la coda: {queue_name}")
        plot_aggregated_averages(queue_name, all_queue_times[queue_name], output_dir)
        plot_comparison_chart(queue_name, all_queue_times[queue_name], output_dir)
        plot_response_time_averages(queue_name, all_response_times[queue_name], output_dir)
        plot_response_times(queue_name, all_queue_times[queue_name], output_dir)

    print(f"\n✅ Analisi completata. Grafici salvati in: {output_dir}/")

if __name__ == "__main__":
    analyze_transient_analysis_directory()
