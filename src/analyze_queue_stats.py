#!/usr/bin/env python3
"""
Script per analizzare e visualizzare le statistiche delle code dal file daily_stats.json
Genera grafici per ogni coda mostrando distribuzione dei tempi di attesa e di esecuzione
Salva tutti i grafici in una cartella senza mostrarli
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict
import pandas as pd
from datetime import datetime

# Configurazione matplotlib per non mostrare grafici
plt.ioff()  # Disabilita la modalità interattiva
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
                # Aggiungi i dati grezzi
                if 'data' in queue_stats:
                    queue_data[queue_name]['queue_times'].extend(queue_stats['data']['queue_time'])
                    queue_data[queue_name]['execution_times'].extend(queue_stats['data']['executing_time'])
                    queue_data[queue_name]['queue_lengths'].extend(queue_stats['data']['queue_lenght'])
                
                # Aggiungi statistiche aggregate per giorno
                queue_data[queue_name]['visits'].append({
                    'date': date,
                    'visited': queue_stats['visited'],
                    'avg_queue_time': queue_stats['queue_time'],
                    'avg_execution_time': queue_stats['executing_time'],
                    'avg_queue_length': queue_stats['queue_lenght']
                })
    
    return queue_data, daily_summaries

def plot_queue_time_distribution(queue_name, queue_times, ax):
    """Plotta la distribuzione dei tempi di attesa per una coda"""
    if not queue_times:
        ax.text(0.5, 0.5, 'Nessun dato di attesa', 
                transform=ax.transAxes, ha='center', va='center')
        return
    
    ax.hist(queue_times, bins=50, alpha=0.7, color='skyblue')
    ax.set_title(f'{queue_name} - Distribuzione Tempi di Attesa')
    ax.set_xlabel('Tempo di Attesa (secondi)')
    ax.set_ylabel('Frequenza')
    ax.grid(True, alpha=0.3)
    
    # Aggiungi statistiche come testo
    mean_time = np.mean(queue_times)
    std_time = np.std(queue_times)
    median_time = np.median(queue_times)
    ax.text(0.02, 0.98, f'Media: {mean_time:.2f}s\nStd: {std_time:.2f}s\nMediana: {median_time:.2f}s', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

def plot_execution_time_distribution(queue_name, execution_times, ax):
    """Plotta la distribuzione dei tempi di esecuzione per una coda"""
    if not execution_times:
        ax.text(0.5, 0.5, 'Nessun dato di esecuzione', 
                transform=ax.transAxes, ha='center', va='center')
        return
    
    ax.hist(execution_times, bins=50, alpha=0.7, color='lightgreen')
    ax.set_title(f'{queue_name} - Distribuzione Tempi di Esecuzione')
    ax.set_xlabel('Tempo di Esecuzione (secondi)')
    ax.set_ylabel('Frequenza')
    ax.grid(True, alpha=0.3)
    
    # Aggiungi statistiche
    mean_time = np.mean(execution_times)
    std_time = np.std(execution_times)
    median_time = np.median(execution_times)
    ax.text(0.02, 0.98, f'Media: {mean_time:.2f}s\nStd: {std_time:.2f}s\nMediana: {median_time:.2f}s', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

def plot_queue_length_over_time(queue_name, queue_lengths, ax):
    """Plotta l'andamento della lunghezza della coda nel tempo"""
    if not queue_lengths:
        ax.text(0.5, 0.5, 'Nessun dato di lunghezza coda', 
                transform=ax.transAxes, ha='center', va='center')
        return
    
    ax.plot(queue_lengths, alpha=0.7, color='orange')
    ax.set_title(f'{queue_name} - Lunghezza Coda nel Tempo')
    ax.set_xlabel('Evento #')
    ax.set_ylabel('Lunghezza Coda')
    ax.grid(True, alpha=0.3)
    
    # Aggiungi statistiche
    mean_length = np.mean(queue_lengths)
    max_length = np.max(queue_lengths)
    ax.text(0.02, 0.98, f'Media: {mean_length:.2f}\nMax: {max_length}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

def plot_boxplot_comparison(queue_data, ax, data_type='queue_times'):
    """Crea un boxplot per confrontare le code"""
    data_to_plot = []
    labels = []
    
    for queue_name, data in queue_data.items():
        if data_type == 'queue_times':
            values = data['queue_times']
        else:
            values = data['execution_times']
        
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
    """Plotta i trend giornalieri"""
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

def create_comprehensive_analysis(filename):
    """Crea un'analisi completa dei dati delle code"""
    # Crea la cartella per i grafici
    output_dir = "queue_analysis_graphs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Carica i dati
    data = load_stats_data(filename)
    queue_data, daily_summaries = extract_queue_data(data)
    
    # Numero di code da analizzare
    queue_names = list(queue_data.keys())
    n_queues = len(queue_names)
    
    print(f"Generando grafici per {n_queues} code...")
    
    # 1. Grafici individuali per ogni coda
    for i, queue_name in enumerate(queue_names):
        print(f"  Generando grafici per {queue_name}...")
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Analisi Completa - {queue_name}', fontsize=16)
        
        # Distribuzione tempi di attesa
        plot_queue_time_distribution(queue_name, queue_data[queue_name]['queue_times'], ax1)
        
        # Distribuzione tempi di esecuzione
        plot_execution_time_distribution(queue_name, queue_data[queue_name]['execution_times'], ax2)
        
        # Lunghezza coda nel tempo
        plot_queue_length_over_time(queue_name, queue_data[queue_name]['queue_lengths'], ax3)
        
        # Scatter plot: tempo attesa vs tempo esecuzione
        queue_times = queue_data[queue_name]['queue_times']
        exec_times = queue_data[queue_name]['execution_times']
        if queue_times and exec_times and len(queue_times) == len(exec_times):
            ax4.scatter(queue_times, exec_times, alpha=0.6)
            ax4.set_xlabel('Tempo di Attesa (s)')
            ax4.set_ylabel('Tempo di Esecuzione (s)')
            ax4.set_title('Correlazione Attesa vs Esecuzione')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Dati non correlabili', 
                    transform=ax4.transAxes, ha='center', va='center')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/analisi_{queue_name.lower()}.png', dpi=300, bbox_inches='tight')
        plt.close()  # Chiudi la figura per liberare memoria
    
    # 2. Grafici di confronto
    print("  Generando grafici di confronto...")
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Confronto tra Code', fontsize=16)
    
    # Boxplot tempi di attesa
    plot_boxplot_comparison(queue_data, ax1, 'queue_times')
    
    # Boxplot tempi di esecuzione
    plot_boxplot_comparison(queue_data, ax2, 'execution_times')
    
    # Trend giornalieri
    plot_daily_trends(daily_summaries, ax3)
    
    # Statistiche aggregate per coda
    queue_stats = []
    for queue_name, data in queue_data.items():
        stats = {
            'Coda': queue_name,
            'Visite Totali': sum([v['visited'] for v in data['visits']]),
            'Tempo Attesa Medio': np.mean(data['queue_times']) if data['queue_times'] else 0,
            'Tempo Esecuzione Medio': np.mean(data['execution_times']) if data['execution_times'] else 0,
            'Lunghezza Media': np.mean(data['queue_lengths']) if data['queue_lengths'] else 0
        }
        queue_stats.append(stats)
    
    # Tabella statistiche
    ax4.axis('tight')
    ax4.axis('off')
    df_stats = pd.DataFrame(queue_stats)
    table = ax4.table(cellText=df_stats.round(2).values, colLabels=df_stats.columns,
                     cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    ax4.set_title('Statistiche Aggregate')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/confronto_code.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Grafico delle utilizzazioni delle code
    print("  Generando grafico utilizzazione code...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Analisi Utilizzo Code', fontsize=16)
    
    # Visite totali per coda
    queue_names_sorted = []
    total_visits = []
    for queue_name, data in queue_data.items():
        queue_names_sorted.append(queue_name)
        total_visits.append(sum([v['visited'] for v in data['visits']]))
    
    ax1.bar(queue_names_sorted, total_visits, color='lightblue')
    ax1.set_title('Visite Totali per Coda')
    ax1.set_ylabel('Numero di Visite')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Tempo medio di servizio per coda
    avg_service_times = []
    for queue_name in queue_names_sorted:
        data = queue_data[queue_name]
        if data['execution_times']:
            avg_service_times.append(np.mean(data['execution_times']))
        else:
            avg_service_times.append(0)
    
    ax2.bar(queue_names_sorted, avg_service_times, color='lightgreen')
    ax2.set_title('Tempo Medio di Servizio per Coda')
    ax2.set_ylabel('Tempo (secondi)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/utilizzo_code.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return queue_data, daily_summaries, output_dir

if __name__ == "__main__":
    # Percorso del file di statistiche
    stats_file = "daily_stats.json"
    
    print("Avvio analisi statistiche delle code...")
    print(f"Caricamento dati da: {stats_file}")
    
    try:
        queue_data, daily_summaries, output_dir = create_comprehensive_analysis(stats_file)
        
        print(f"\n=== ANALISI COMPLETATA ===")
        print(f"Code analizzate: {len(queue_data)}")
        print(f"Giorni simulati: {len(daily_summaries)}")
        print(f"Grafici salvati in: {output_dir}/")
        
        # Riepilogo per ogni coda
        print(f"\n=== RIEPILOGO CODE ===")
        for queue_name, data in queue_data.items():
            total_events = len(data['queue_times'])
            avg_queue_time = np.mean(data['queue_times']) if data['queue_times'] else 0
            avg_exec_time = np.mean(data['execution_times']) if data['execution_times'] else 0
            total_visits = sum([v['visited'] for v in data['visits']])
            
            print(f"{queue_name}:")
            print(f"  - Eventi totali: {total_events}")
            print(f"  - Visite totali: {total_visits}")
            print(f"  - Tempo attesa medio: {avg_queue_time:.2f}s")
            print(f"  - Tempo esecuzione medio: {avg_exec_time:.2f}s")
        
        # Lista dei file generati
        print(f"\n=== FILE GENERATI ===")
        for queue_name in queue_data.keys():
            print(f"- {output_dir}/analisi_{queue_name.lower()}.png")
        print(f"- {output_dir}/confronto_code.png")
        print(f"- {output_dir}/utilizzo_code.png")
        
    except FileNotFoundError:
        print(f"Errore: File {stats_file} non trovato!")
        print("Assicurati che il file sia nella directory corrente")
    except Exception as e:
        print(f"Errore durante l'analisi: {e}")
        import traceback
        traceback.print_exc()
