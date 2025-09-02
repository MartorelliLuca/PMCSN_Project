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
        'visits': []
    })
    daily_summaries = []
    for entry in data:
        if entry['type'] == 'daily_summary':
            date = entry['date']
            daily_summaries.append({
                'date': date,
                'entrati': entry['summary']['entrati'],
                'usciti': entry['summary']['usciti'],
                'coda_piena': entry['summary']['trovato_coda_piena']
            })
            stats = entry['stats']
            for queue_name, queue_stats in stats.items():
                if 'data' in queue_stats:
                    queue_data[queue_name]['queue_times'].extend(queue_stats['data']['queue_time'])
                    queue_data[queue_name]['execution_times'].extend(queue_stats['data']['executing_time'])
                    queue_data[queue_name]['queue_lengths'].extend(queue_stats['data']['queue_lenght'])
                queue_data[queue_name]['visits'].append({
                    'date': date,
                    'visited': queue_stats['visited'],
                    'avg_queue_time': queue_stats['queue_time'],
                    'avg_execution_time': queue_stats['executing_time'],
                    'avg_queue_length': queue_stats['queue_lenght']
                })
    return queue_data, daily_summaries

def analyze_transient_analysis_directory(transient_dir="transient_analysis_json", output_dir="graphs/transient_avg"):
    if not os.path.exists(transient_dir):
        print(f"Directory {transient_dir}/ non trovata. Nessuna analisi eseguita.")
        return

    json_files = [os.path.join(transient_dir, f) for f in os.listdir(transient_dir)
                  if f.endswith(".json") and f.startswith("rep")]
    if not json_files:
        print(f"Nessun file JSON valido trovato in {transient_dir}/. Nessuna analisi eseguita.")
        return

    print(f"\n📊 Analisi transitoria: trovati {len(json_files)} file in {transient_dir}/")

    all_queue_data = defaultdict(lambda: {
        'queue_times': [],
        'execution_times': [],
        'queue_lengths': [],
        'visits': []
    })
    all_daily_summaries = []
    per_replica_data = []

    for file in json_files:
        print(f"  Caricamento {file} ...")
        data = load_stats_data(file)
        queue_data, daily_summaries = extract_queue_data(data)
        per_replica_data.append((os.path.basename(file), queue_data, daily_summaries))
        for qname, qdata in queue_data.items():
            all_queue_data[qname]['queue_times'].extend(qdata['queue_times'])
            all_queue_data[qname]['execution_times'].extend(qdata['execution_times'])
            all_queue_data[qname]['queue_lengths'].extend(qdata['queue_lengths'])
            all_queue_data[qname]['visits'].extend(qdata['visits'])
        all_daily_summaries.extend(daily_summaries)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    queue_names = list(all_queue_data.keys())

    print("\n📈 Generazione grafici medi su tutte le repliche...")
    for qname in queue_names:
        fig, ax = plt.subplots(figsize=(12, 6))
        for rep_name, queue_data, _ in per_replica_data:
            q_times = queue_data.get(qname, {}).get('queue_times', [])
            if q_times:
                avg = np.mean(q_times)
                ax.bar(rep_name.replace(".json", ""), avg)
        ax.set_title(f"{qname} - Media dei Tempi di Attesa per Replica")
        ax.set_ylabel("Tempo di Attesa Medio (s)")
        ax.set_xlabel("Replica")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/media_attesa_{qname.lower()}.png", dpi=300)
        plt.close()

    print("\n📊 Generazione grafici di confronto tra repliche...")
    for qname in queue_names:
        fig, ax = plt.subplots(figsize=(12, 6))
        for rep_name, queue_data, _ in per_replica_data:
            q_times = queue_data.get(qname, {}).get('queue_times', [])
            if q_times:
                moving_avg = pd.Series(q_times).rolling(window=max(10, len(q_times)//50)).mean()
                ax.plot(moving_avg, label=rep_name.replace(".json", ""))
        ax.set_title(f'{qname} - Confronto tra repliche (Media Mobile)')
        ax.set_xlabel('Evento #')
        ax.set_ylabel('Tempo di Attesa (s)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/confronto_{qname.lower()}.png", dpi=300)
        plt.close()

    print(f"\n✅ Analisi completata. Grafici salvati in: {output_dir}/")

if __name__ == "__main__":
    analyze_transient_analysis_directory()
