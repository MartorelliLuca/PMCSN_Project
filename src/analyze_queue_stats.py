"""
Script per analizzare e visualizzare le statistiche delle code dal file daily_stats.json
Genera grafici per ogni coda e salva i risultati in una cartella specificata da --mode
"""

import json
import shutil
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict
import pandas as pd
from datetime import datetime
import argparse

# Configurazione matplotlib per non mostrare grafici
plt.ioff()
plt.style.use('default')

def load_stats_data(filename):
    """Carica i dati dal file JSON delle statistiche"""
    data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def extract_queue_data(data):
    """Estrae i dati delle code da tutti i giorni"""
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

def plot_queue_time_distribution(queue_name, queue_times, ax):
    if not queue_times:
        ax.text(0.5, 0.5, 'Nessun dato di attesa', 
                transform=ax.transAxes, ha='center', va='center')
        return
    ax.hist(queue_times, bins=50, alpha=0.7, color='skyblue')
    ax.set_title(f'{queue_name} - Distribuzione Tempi di Attesa')
    ax.set_xlabel('Tempo di Attesa (secondi)')
    ax.set_ylabel('Frequenza')
    ax.grid(True, alpha=0.3)
    mean_time = np.mean(queue_times)
    std_time = np.std(queue_times)
    median_time = np.median(queue_times)
    ax.text(0.02, 0.98, f'Media: {mean_time:.2f}s\nStd: {std_time:.2f}s\nMediana: {median_time:.2f}s', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

def plot_execution_time_distribution(queue_name, execution_times, ax):
    if not execution_times:
        ax.text(0.5, 0.5, 'Nessun dato di esecuzione', 
                transform=ax.transAxes, ha='center', va='center')
        return
    ax.hist(execution_times, bins=50, alpha=0.7, color='lightgreen')
    ax.set_title(f'{queue_name} - Distribuzione Tempi di Esecuzione')
    ax.set_xlabel('Tempo di Esecuzione (secondi)')
    ax.set_ylabel('Frequenza')
    ax.grid(True, alpha=0.3)
    mean_time = np.mean(execution_times)
    std_time = np.std(execution_times)
    median_time = np.median(execution_times)
    ax.text(0.02, 0.98, f'Media: {mean_time:.2f}s\nStd: {std_time:.2f}s\nMediana: {median_time:.2f}s', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

def plot_queue_length_over_time(queue_name, queue_lengths, ax):
    if not queue_lengths:
        ax.text(0.5, 0.5, 'Nessun dato di lunghezza coda', 
                transform=ax.transAxes, ha='center', va='center')
        return
    ax.plot(queue_lengths, alpha=0.7, color='orange')
    ax.set_title(f'{queue_name} - Lunghezza Coda nel Tempo')
    ax.set_xlabel('Evento #')
    ax.set_ylabel('Lunghezza Coda')
    ax.grid(True, alpha=0.3)
    mean_length = np.mean(queue_lengths)
    max_length = np.max(queue_lengths)
    ax.text(0.02, 0.98, f'Media: {mean_length:.2f}\nMax: {max_length}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

def plot_wait_times_over_time(queue_name, queue_times, ax):
    """Plotta solo la media mobile dei tempi di attesa"""
    if not queue_times or len(queue_times) < 10:
        ax.text(0.5, 0.5, 'Dati insufficienti per media mobile', 
                transform=ax.transAxes, ha='center', va='center')
        return
    time_indices = range(len(queue_times))
    window_size = max(10, len(queue_times) // 50)
    moving_avg = []
    for i in range(len(queue_times)):
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(queue_times), i + window_size // 2 + 1)
        moving_avg.append(np.mean(queue_times[start_idx:end_idx]))
    ax.plot(time_indices, moving_avg, color='darkred', linewidth=2, 
            label=f'Media Mobile (finestra={window_size})')
    ax.legend(loc='upper right')
    ax.set_title(f'{queue_name} - Tempi di Attesa (Media Mobile)')
    ax.set_xlabel('Evento # (Sequenza Temporale)')
    ax.set_ylabel('Tempo di Attesa (secondi)')
    ax.grid(True, alpha=0.3)
    mean_time = np.mean(queue_times)
    max_time = np.max(queue_times)
    std_time = np.std(queue_times)
    max_idx = np.argmax(queue_times)
    stats_text = f'Media: {mean_time:.2f}s\nMax: {max_time:.2f}s (evento #{max_idx})\nStd: {std_time:.2f}s'
    ax.text(0.02, 0.98, stats_text, 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

def plot_temporal_analysis(queue_name, queue_data, ax):
    queue_times = queue_data['queue_times']
    if not queue_times or len(queue_times) < 10:
        ax.text(0.5, 0.5, 'Dati insufficienti per analisi temporale', 
                transform=ax.transAxes, ha='center', va='center')
        return
    n_segments = min(20, len(queue_times) // 10)
    if n_segments < 2:
        n_segments = 2
    segment_size = len(queue_times) // n_segments
    segment_means = []
    segment_labels = []
    for i in range(n_segments):
        start_idx = i * segment_size
        end_idx = (i + 1) * segment_size if i < n_segments - 1 else len(queue_times)
        segment_data = queue_times[start_idx:end_idx]
        if segment_data:
            segment_means.append(np.mean(segment_data))
            segment_labels.append(f'{i+1}')
        else:
            segment_means.append(0)
            segment_labels.append(f'{i+1}')
    colors = ['red' if mean > np.mean(queue_times) * 1.5 else 
              'orange' if mean > np.mean(queue_times) * 1.2 else 
              'green' for mean in segment_means]
    ax.bar(segment_labels, segment_means, color=colors, alpha=0.7)
    ax.set_title(f'{queue_name} - Analisi Periodi Temporali')
    ax.set_xlabel('Periodo Temporale')
    ax.set_ylabel('Tempo Attesa Medio (s)')
    ax.grid(True, alpha=0.3)
    global_mean = np.mean(queue_times)
    ax.axhline(y=global_mean, color='black', linestyle='--', alpha=0.7, 
               label=f'Media Globale: {global_mean:.2f}s')
    ax.legend()
    max_idx = np.argmax(segment_means)
    max_value = segment_means[max_idx]
    ax.text(0.02, 0.98, f'Periodo più critico: #{max_idx+1}\nTempo medio: {max_value:.2f}s', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

def plot_boxplot_comparison(queue_data, ax, data_type='queue_times'):
    data_to_plot = []
    labels = []
    for queue_name, data in queue_data.items():
        values = data['queue_times'] if data_type == 'queue_times' else data['execution_times']
        if values:
            data_to_plot.append(values)
            labels.append(queue_name)
    if data_to_plot:
        ax.boxplot(data_to_plot, labels=labels)
        title = 'Confronto Tempi di Attesa' if data_type == 'queue_times' else 'Confronto Tempi di Esecuzione'
        ax.set_title(title)
        ax.set_ylabel('Tempo (secondi)')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)

def plot_daily_trends(daily_summaries, ax):
    dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_summaries]
    entrati = [d['entrati'] for d in daily_summaries]
    usciti = [d['usciti'] for d in daily_summaries]
    ax.plot(dates, entrati, 'o-', label='Entrati', color='green')
    ax.plot(dates, usciti, 's-', label='Usciti', color='blue')
    ax.set_title('Trend Giornalieri - Entrati vs Usciti')
    ax.set_xlabel('Data')
    ax.set_ylabel('Numero di Entità')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

def create_comprehensive_analysis(filename, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    data = load_stats_data(filename)
    queue_data, daily_summaries = extract_queue_data(data)
    queue_names = list(queue_data.keys())
    print(f"Generando grafici per {len(queue_names)} code...")
    for i, queue_name in enumerate(queue_names):
        print(f"  Generando grafici per {queue_name}...")
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle(f'Analisi Completa - {queue_name}', fontsize=16)
        plot_queue_time_distribution(queue_name, queue_data[queue_name]['queue_times'], axes[0,0])
        plot_execution_time_distribution(queue_name, queue_data[queue_name]['execution_times'], axes[0,1])
        plot_wait_times_over_time(queue_name, queue_data[queue_name]['queue_times'], axes[0,2])
        plot_queue_length_over_time(queue_name, queue_data[queue_name]['queue_lengths'], axes[1,0])
        queue_times = queue_data[queue_name]['queue_times']
        exec_times = queue_data[queue_name]['execution_times']
        if queue_times and exec_times and len(queue_times) == len(exec_times):
            axes[1,1].scatter(queue_times, exec_times, alpha=0.6)
            axes[1,1].set_xlabel('Tempo di Attesa (s)')
            axes[1,1].set_ylabel('Tempo di Esecuzione (s)')
            axes[1,1].set_title('Correlazione Attesa vs Esecuzione')
            axes[1,1].grid(True, alpha=0.3)
        else:
            axes[1,1].text(0.5, 0.5, 'Dati non correlabili', 
                           transform=axes[1,1].transAxes, ha='center', va='center')
        plot_temporal_analysis(queue_name, queue_data[queue_name], axes[1,2])
        plt.tight_layout()
        plt.savefig(f'{output_dir}/analisi_{queue_name.lower()}.png', dpi=300, bbox_inches='tight')
        plt.close()
    return queue_data, daily_summaries, output_dir


def analyze_transient_analysis_directory(transient_dir="transient_analysis_json", output_dir="graphs/transient_avg"):
    """
    Analizza tutti i file JSON nella directory transient_analysis_json/,
    genera sia grafici medi che grafici di confronto tra repliche.
    """
    if not os.path.exists(transient_dir):
        print(f"Directory {transient_dir}/ non trovata. Nessuna analisi eseguita.")
        return
    
    json_files = [os.path.join(transient_dir, f) for f in os.listdir(transient_dir) if f.endswith(".json")]
    if not json_files:
        print(f"Nessun file JSON trovato in {transient_dir}/. Nessuna analisi eseguita.")
        return

    print(f"\n📊 Analisi transitoria: trovati {len(json_files)} file in {transient_dir}/")
    
    # Dati globali
    all_queue_data = defaultdict(lambda: {
        'queue_times': [],
        'execution_times': [],
        'queue_lengths': [],
        'visits': []
    })
    all_daily_summaries = []

    # Dati per replica (serve per confronti)
    per_replica_data = []

    for file in json_files:
        print(f"  Caricamento {file} ...")
        data = load_stats_data(file)
        queue_data, daily_summaries = extract_queue_data(data)

        per_replica_data.append((os.path.basename(file), queue_data, daily_summaries))

        # Aggiungi ai dataset globali
        for qname, qdata in queue_data.items():
            all_queue_data[qname]['queue_times'].extend(qdata['queue_times'])
            all_queue_data[qname]['execution_times'].extend(qdata['execution_times'])
            all_queue_data[qname]['queue_lengths'].extend(qdata['queue_lengths'])
            all_queue_data[qname]['visits'].extend(qdata['visits'])
        all_daily_summaries.extend(daily_summaries)

    # Genera cartella output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- 1) Grafici medi ---
    print("\n📈 Generazione grafici medi su tutte le repliche...")
    queue_names = list(all_queue_data.keys())
    for qname in queue_names:
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle(f'Analisi Media - {qname}', fontsize=16)

        plot_queue_time_distribution(qname, all_queue_data[qname]['queue_times'], axes[0,0])
        plot_execution_time_distribution(qname, all_queue_data[qname]['execution_times'], axes[0,1])
        plot_wait_times_over_time(qname, all_queue_data[qname]['queue_times'], axes[0,2])
        plot_queue_length_over_time(qname, all_queue_data[qname]['queue_lengths'], axes[1,0])

        # Correlazione
        queue_times = all_queue_data[qname]['queue_times']
        exec_times = all_queue_data[qname]['execution_times']
        if queue_times and exec_times and len(queue_times) == len(exec_times):
            axes[1,1].scatter(queue_times, exec_times, alpha=0.6)
            axes[1,1].set_xlabel('Tempo di Attesa (s)')
            axes[1,1].set_ylabel('Tempo di Esecuzione (s)')
            axes[1,1].set_title('Correlazione Attesa vs Esecuzione')
            axes[1,1].grid(True, alpha=0.3)
        else:
            axes[1,1].text(0.5, 0.5, 'Dati non correlabili',
                           transform=axes[1,1].transAxes, ha='center', va='center')

        plot_temporal_analysis(qname, all_queue_data[qname], axes[1,2])

        plt.tight_layout()
        plt.savefig(f"{output_dir}/analisi_media_{qname.lower()}.png", dpi=300, bbox_inches='tight')
        plt.close()

    # --- 2) Grafici di confronto ---
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
        plt.savefig(f"{output_dir}/confronto_{qname.lower()}.png", dpi=300, bbox_inches='tight')
        plt.close()

    print(f"\n✅ Analisi completata: medie + confronti.")
    print(f"📁 Grafici salvati in: {output_dir}/")


if __name__ == "__main__":
    # Path al file di configurazione
    config_file = "../conf/input.json"
    
    # Carica il path globale da input.json
    with open(config_file, "r") as f:
        config = json.load(f)
    base_path = config.get("output_path", "graphs")  # default: graphs
    
    # Chiedi il nome cartella da input
    folder_name = input("Inserisci il nome della cartella per i grafici: ").strip()
    output_dir = os.path.join(base_path, folder_name)

    stats_file = "daily_stats.json"
    
    print("Avvio analisi statistiche delle code...")
    print(f"Caricamento dati da: {stats_file}")
    print(f"Cartella di output: {output_dir}/")
    
    try:
        queue_data, daily_summaries, output_dir = create_comprehensive_analysis(stats_file, output_dir)
        
        if os.path.exists(config_file):
            shutil.copy(config_file, os.path.join(output_dir, "input.json"))
            print(f"File input.json copiato in {output_dir}/")
        else:
            print("Attenzione: input.json non trovato, nessuna copia effettuata.")
        
        print(f"\n=== ANALISI COMPLETATA ===")
        print(f"Code analizzate: {len(queue_data)}")
        print(f"Giorni simulati: {len(daily_summaries)}")
        print(f"Grafici e input.json salvati in: {output_dir}/")
        
    except FileNotFoundError:
        print(f"Errore: File {stats_file} non trovato!")
    except Exception as e:
        print(f"Errore durante l'analisi: {e}")
        import traceback
        traceback.print_exc()
    
    # 🔥 Analisi media di tutte le repliche transienti
    analyze_transient_analysis_directory()
