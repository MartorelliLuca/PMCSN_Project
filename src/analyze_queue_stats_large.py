#!/usr/bin/env python3
"""
Enhanced queue analysis script for large datasets (3-4 months of data)
Optimized for memory efficiency and temporal analysis
"""

import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from collections import defaultdict
import pandas as pd
from datetime import datetime, timedelta
import gc
from matplotlib.colors import LinearSegmentedColormap

# Configurazione matplotlib per non mostrare grafici
plt.ioff()
plt.style.use('default')
plt.rcParams['figure.max_open_warning'] = 0  # Disabilita warning per troppe figure aperte

class LargeDatasetAnalyzer:
    def __init__(self, filename, chunk_size=1000):
        self.filename = filename
        self.chunk_size = chunk_size
        self.queue_data = defaultdict(lambda: {
            'daily_stats': [],  # Per analisi temporale
            'queue_times': [],
            'execution_times': [],
            'queue_lengths': [],
            'visits': []
        })
        self.daily_summaries = []
        
    def load_stats_data_chunked(self):
        """Carica i dati in chunk per gestire file grandi"""
        print("Caricamento dati in modalità ottimizzata...")
        
        with open(self.filename, 'r') as f:
            chunk = []
            for line_num, line in enumerate(f):
                if line.strip():
                    try:
                        data = json.loads(line)
                        chunk.append(data)
                        
                        if len(chunk) >= self.chunk_size:
                            self._process_chunk(chunk)
                            chunk = []
                            
                    except json.JSONDecodeError as e:
                        print(f"Errore JSON alla riga {line_num}: {e}")
                        continue
                        
            # Processa l'ultimo chunk
            if chunk:
                self._process_chunk(chunk)
                
        print(f"Caricati {len(self.daily_summaries)} giorni di dati")
        
    def _process_chunk(self, chunk):
        """Processa un chunk di dati"""
        for entry in chunk:
            if entry['type'] == 'daily_summary':
                date = entry['date']
                
                # Salva summary giornaliero
                self.daily_summaries.append({
                    'date': date,
                    'entrati': entry['summary']['entrati'],
                    'usciti': entry['summary']['usciti'],
                    'coda_piena': entry['summary']['trovato_coda_piena']
                })
                
                # Processa statistiche delle code
                stats = entry['stats']
                for queue_name, queue_stats in stats.items():
                    
                    # Salva statistiche giornaliere per analisi temporale
                    self.queue_data[queue_name]['daily_stats'].append({
                        'date': date,
                        'visited': queue_stats['visited'],
                        'avg_queue_time': queue_stats['queue_time'],
                        'avg_execution_time': queue_stats['executing_time'],
                        'avg_queue_length': queue_stats['queue_lenght']
                    })
                    
                    # Aggiungi solo un campione dei dati dettagliati per evitare overflow di memoria
                    if 'data' in queue_stats:
                        # Campiona i dati se il dataset è troppo grande
                        sample_size = min(100, len(queue_stats['data']['queue_time']))
                        if len(queue_stats['data']['queue_time']) > sample_size:
                            indices = np.random.choice(len(queue_stats['data']['queue_time']), 
                                                     sample_size, replace=False)
                            sampled_queue_times = [queue_stats['data']['queue_time'][i] for i in indices]
                            sampled_exec_times = [queue_stats['data']['executing_time'][i] for i in indices]
                            sampled_queue_lengths = [queue_stats['data']['queue_lenght'][i] for i in indices]
                        else:
                            sampled_queue_times = queue_stats['data']['queue_time']
                            sampled_exec_times = queue_stats['data']['executing_time']
                            sampled_queue_lengths = queue_stats['data']['queue_lenght']
                            
                        self.queue_data[queue_name]['queue_times'].extend(sampled_queue_times)
                        self.queue_data[queue_name]['execution_times'].extend(sampled_exec_times)
                        self.queue_data[queue_name]['queue_lengths'].extend(sampled_queue_lengths)
                    
                    # Aggiungi visit info
                    self.queue_data[queue_name]['visits'].append({
                        'date': date,
                        'visited': queue_stats['visited'],
                        'avg_queue_time': queue_stats['queue_time'],
                        'avg_execution_time': queue_stats['executing_time'],
                        'avg_queue_length': queue_stats['queue_lenght']
                    })
        
        # Forza garbage collection per liberare memoria
        gc.collect()

    def plot_temporal_analysis(self, output_dir):
        """Crea grafici temporali per mostrare l'andamento del sistema nel tempo"""
        print("  Generando analisi temporale del sistema...")
        
        # Converte le date in datetime objects
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in self.daily_summaries]
        
        # 1. Grafico temporale generale del sistema
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle('Analisi Temporale del Sistema', fontsize=16)
        
        # Entrati vs Usciti nel tempo
        entrati = [d['entrati'] for d in self.daily_summaries]
        usciti = [d['usciti'] for d in self.daily_summaries]
        
        ax1.plot(dates, entrati, 'o-', label='Entrati', color='green', alpha=0.7)
        ax1.plot(dates, usciti, 's-', label='Usciti', color='blue', alpha=0.7)
        ax1.set_title('Throughput Giornaliero')
        ax1.set_ylabel('Numero di Entità')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.tick_params(axis='x', rotation=45)
        
        # Efficienza del sistema (usciti/entrati)
        efficiency = [u/e if e > 0 else 0 for e, u in zip(entrati, usciti)]
        ax2.plot(dates, efficiency, 'ro-', alpha=0.7)
        ax2.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='Efficienza 100%')
        ax2.set_title('Efficienza del Sistema (Usciti/Entrati)')
        ax2.set_ylabel('Efficienza')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.tick_params(axis='x', rotation=45)
        
        # Visite totali per coda nel tempo
        queue_names = list(self.queue_data.keys())
        colors = plt.cm.Set3(np.linspace(0, 1, len(queue_names)))
        
        for i, queue_name in enumerate(queue_names):
            daily_visits = []
            queue_dates = []
            
            for visit_data in self.queue_data[queue_name]['visits']:
                if visit_data['date'] in [d['date'] for d in self.daily_summaries]:
                    daily_visits.append(visit_data['visited'])
                    queue_dates.append(datetime.strptime(visit_data['date'], '%Y-%m-%d'))
            
            if daily_visits:
                ax3.plot(queue_dates, daily_visits, 'o-', label=queue_name, 
                        color=colors[i], alpha=0.7)
        
        ax3.set_title('Visite Giornaliere per Coda')
        ax3.set_ylabel('Numero di Visite')
        ax3.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax3.tick_params(axis='x', rotation=45)
        
        # Tempo medio di attesa per coda nel tempo
        for i, queue_name in enumerate(queue_names):
            daily_queue_times = []
            queue_dates = []
            
            for visit_data in self.queue_data[queue_name]['visits']:
                if visit_data['date'] in [d['date'] for d in self.daily_summaries]:
                    daily_queue_times.append(visit_data['avg_queue_time'])
                    queue_dates.append(datetime.strptime(visit_data['date'], '%Y-%m-%d'))
            
            if daily_queue_times and any(t > 0 for t in daily_queue_times):
                ax4.plot(queue_dates, daily_queue_times, 'o-', label=queue_name, 
                        color=colors[i], alpha=0.7)
        
        ax4.set_title('Tempo Medio di Attesa per Coda')
        ax4.set_ylabel('Tempo di Attesa (s)')
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.grid(True, alpha=0.3)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/analisi_temporale_sistema.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_queue_performance_heatmap(self, output_dir):
        """Crea una heatmap delle performance delle code nel tempo"""
        print("  Generando heatmap performance code...")
        
        queue_names = list(self.queue_data.keys())
        dates = sorted(list(set([v['date'] for queue_data in self.queue_data.values() 
                                for v in queue_data['visits']])))
        
        # Crea matrici per heatmap
        utilization_matrix = np.zeros((len(queue_names), len(dates)))
        queue_time_matrix = np.zeros((len(queue_names), len(dates)))
        
        for i, queue_name in enumerate(queue_names):
            for j, date in enumerate(dates):
                # Trova i dati per questa data
                day_data = [v for v in self.queue_data[queue_name]['visits'] if v['date'] == date]
                if day_data:
                    utilization_matrix[i, j] = day_data[0]['visited']
                    queue_time_matrix[i, j] = day_data[0]['avg_queue_time']
        
        # Crea heatmap
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10))
        fig.suptitle('Heatmap Performance Code nel Tempo', fontsize=16)
        
        # Heatmap utilizzo (numero di visite)
        im1 = ax1.imshow(utilization_matrix, aspect='auto', cmap='YlOrRd', interpolation='nearest')
        ax1.set_title('Utilizzo Code (Numero di Visite)')
        ax1.set_ylabel('Code')
        ax1.set_yticks(range(len(queue_names)))
        ax1.set_yticklabels(queue_names)
        
        # Configura asse x per le date (mostra solo alcune date per leggibilità)
        date_indices = range(0, len(dates), max(1, len(dates)//10))
        ax1.set_xticks(date_indices)
        ax1.set_xticklabels([dates[i] for i in date_indices], rotation=45)
        
        plt.colorbar(im1, ax=ax1, label='Numero di Visite')
        
        # Heatmap tempi di attesa
        im2 = ax2.imshow(queue_time_matrix, aspect='auto', cmap='Reds', interpolation='nearest')
        ax2.set_title('Tempi di Attesa Medi')
        ax2.set_ylabel('Code')
        ax2.set_xlabel('Data')
        ax2.set_yticks(range(len(queue_names)))
        ax2.set_yticklabels(queue_names)
        ax2.set_xticks(date_indices)
        ax2.set_xticklabels([dates[i] for i in date_indices], rotation=45)
        
        plt.colorbar(im2, ax=ax2, label='Tempo di Attesa (s)')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/heatmap_performance_code.png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_weekly_monthly_trends(self, output_dir):
        """Analizza trend settimanali e mensili"""
        print("  Generando analisi trend settimanali/mensili...")
        
        # Converte date e calcola giorno della settimana e mese
        df_summaries = pd.DataFrame(self.daily_summaries)
        df_summaries['date'] = pd.to_datetime(df_summaries['date'])
        df_summaries['weekday'] = df_summaries['date'].dt.day_name()
        df_summaries['month'] = df_summaries['date'].dt.strftime('%Y-%m')
        df_summaries['week'] = df_summaries['date'].dt.isocalendar().week
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle('Analisi Trend Temporali', fontsize=16)
        
        # Trend per giorno della settimana
        weekday_stats = df_summaries.groupby('weekday').agg({
            'entrati': 'mean',
            'usciti': 'mean'
        }).reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        
        weekday_stats.plot(kind='bar', ax=ax1, color=['green', 'blue'], alpha=0.7)
        ax1.set_title('Media Giornaliera per Giorno della Settimana')
        ax1.set_ylabel('Numero Medio di Entità')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Trend mensile
        monthly_stats = df_summaries.groupby('month').agg({
            'entrati': 'sum',
            'usciti': 'sum'
        })
        
        monthly_stats.plot(kind='line', ax=ax2, marker='o', color=['green', 'blue'], alpha=0.7)
        ax2.set_title('Totali Mensili')
        ax2.set_ylabel('Numero Totale di Entità')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Distribuzione oraria simulata (se disponibile)
        # Per ora mostra la distribuzione delle visite per coda
        queue_names = list(self.queue_data.keys())
        total_visits = [sum([v['visited'] for v in self.queue_data[q]['visits']]) for q in queue_names]
        
        ax3.pie(total_visits, labels=queue_names, autopct='%1.1f%%', startangle=90)
        ax3.set_title('Distribuzione Visite per Coda (Totale)')
        
        # Efficienza nel tempo
        df_summaries['efficiency'] = df_summaries['usciti'] / df_summaries['entrati'].replace(0, 1)
        df_summaries.set_index('date')['efficiency'].plot(ax=ax4, color='red', alpha=0.7)
        ax4.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='Efficienza 100%')
        ax4.set_title('Efficienza del Sistema nel Tempo')
        ax4.set_ylabel('Efficienza (Usciti/Entrati)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/trend_temporali.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_comprehensive_analysis(self):
        """Crea analisi completa ottimizzata per grandi dataset"""
        # Crea cartella output
        output_dir = "queue_analysis_graphs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Carica dati
        self.load_stats_data_chunked()
        
        # Analisi temporali avanzate
        self.plot_temporal_analysis(output_dir)
        self.plot_queue_performance_heatmap(output_dir)
        self.plot_weekly_monthly_trends(output_dir)
        
        # Analisi tradizionali (ottimizzate)
        self._create_optimized_individual_analysis(output_dir)
        self._create_optimized_comparison_analysis(output_dir)
        
        return output_dir

    def _create_optimized_individual_analysis(self, output_dir):
        """Crea analisi individuali ottimizzate per memoria"""
        print("  Generando analisi individuali ottimizzate...")
        
        queue_names = list(self.queue_data.keys())
        
        for queue_name in queue_names:
            print(f"    Processando {queue_name}...")
            
            # Usa solo un campione se i dati sono troppi
            queue_times = self.queue_data[queue_name]['queue_times']
            exec_times = self.queue_data[queue_name]['execution_times']
            queue_lengths = self.queue_data[queue_name]['queue_lengths']
            
            # Campiona se necessario
            max_points = 10000
            if len(queue_times) > max_points:
                indices = np.random.choice(len(queue_times), max_points, replace=False)
                queue_times = [queue_times[i] for i in indices]
                exec_times = [exec_times[i] for i in indices] if exec_times else []
                queue_lengths = [queue_lengths[i] for i in indices] if queue_lengths else []
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'Analisi Ottimizzata - {queue_name}', fontsize=16)
            
            # Distribuzione tempi di attesa
            if queue_times:
                ax1.hist(queue_times, bins=min(50, len(queue_times)//10), alpha=0.7, color='skyblue')
                ax1.set_title('Distribuzione Tempi di Attesa')
                ax1.set_xlabel('Tempo di Attesa (s)')
                ax1.set_ylabel('Frequenza')
                ax1.grid(True, alpha=0.3)
                
                mean_time = np.mean(queue_times)
                std_time = np.std(queue_times)
                ax1.text(0.02, 0.98, f'Media: {mean_time:.2f}s\nStd: {std_time:.2f}s', 
                        transform=ax1.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Distribuzione tempi di esecuzione
            if exec_times:
                ax2.hist(exec_times, bins=min(50, len(exec_times)//10), alpha=0.7, color='lightgreen')
                ax2.set_title('Distribuzione Tempi di Esecuzione')
                ax2.set_xlabel('Tempo di Esecuzione (s)')
                ax2.set_ylabel('Frequenza')
                ax2.grid(True, alpha=0.3)
                
                mean_exec = np.mean(exec_times)
                std_exec = np.std(exec_times)
                ax2.text(0.02, 0.98, f'Media: {mean_exec:.2f}s\nStd: {std_exec:.2f}s', 
                        transform=ax2.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Andamento temporale delle visite
            dates = [datetime.strptime(v['date'], '%Y-%m-%d') for v in self.queue_data[queue_name]['visits']]
            visits = [v['visited'] for v in self.queue_data[queue_name]['visits']]
            
            ax3.plot(dates, visits, 'o-', alpha=0.7, color='orange')
            ax3.set_title('Visite nel Tempo')
            ax3.set_xlabel('Data')
            ax3.set_ylabel('Numero di Visite')
            ax3.grid(True, alpha=0.3)
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            
            # Correlazione attesa vs esecuzione (campionata)
            if queue_times and exec_times and len(queue_times) == len(exec_times):
                sample_size = min(1000, len(queue_times))
                if len(queue_times) > sample_size:
                    indices = np.random.choice(len(queue_times), sample_size, replace=False)
                    sample_queue = [queue_times[i] for i in indices]
                    sample_exec = [exec_times[i] for i in indices]
                else:
                    sample_queue = queue_times
                    sample_exec = exec_times
                
                ax4.scatter(sample_queue, sample_exec, alpha=0.6, s=1)
                ax4.set_xlabel('Tempo di Attesa (s)')
                ax4.set_ylabel('Tempo di Esecuzione (s)')
                ax4.set_title(f'Correlazione (campione di {len(sample_queue)} punti)')
                ax4.grid(True, alpha=0.3)
            else:
                ax4.text(0.5, 0.5, 'Dati non correlabili', 
                        transform=ax4.transAxes, ha='center', va='center')
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/analisi_{queue_name.lower()}.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Forza garbage collection
            gc.collect()

    def _create_optimized_comparison_analysis(self, output_dir):
        """Crea analisi di confronto ottimizzate"""
        print("  Generando confronti ottimizzati...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Confronto Code - Analisi Ottimizzata', fontsize=16)
        
        # Boxplot tempi di attesa (campionati)
        queue_names = list(self.queue_data.keys())
        data_to_plot = []
        labels = []
        
        for queue_name in queue_names:
            queue_times = self.queue_data[queue_name]['queue_times']
            if queue_times:
                # Campiona per il boxplot
                sample_size = min(1000, len(queue_times))
                if len(queue_times) > sample_size:
                    sampled = np.random.choice(queue_times, sample_size, replace=False)
                else:
                    sampled = queue_times
                data_to_plot.append(sampled)
                labels.append(queue_name)
        
        if data_to_plot:
            ax1.boxplot(data_to_plot, tick_labels=labels)
            ax1.set_title('Confronto Tempi di Attesa')
            ax1.set_ylabel('Tempo (s)')
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, alpha=0.3)
        
        # Visite totali per coda
        total_visits = []
        for queue_name in queue_names:
            total = sum([v['visited'] for v in self.queue_data[queue_name]['visits']])
            total_visits.append(total)
        
        ax2.bar(queue_names, total_visits, color='lightblue', alpha=0.7)
        ax2.set_title('Visite Totali per Coda')
        ax2.set_ylabel('Numero di Visite')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Efficienza nel tempo
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in self.daily_summaries]
        entrati = [d['entrati'] for d in self.daily_summaries]
        usciti = [d['usciti'] for d in self.daily_summaries]
        efficiency = [u/e if e > 0 else 0 for e, u in zip(entrati, usciti)]
        
        ax3.plot(dates, efficiency, 'ro-', alpha=0.7)
        ax3.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
        ax3.set_title('Efficienza Sistema')
        ax3.set_ylabel('Efficienza')
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        # Tabella riassuntiva
        ax4.axis('tight')
        ax4.axis('off')
        
        summary_data = []
        for queue_name in queue_names:
            total_visits = sum([v['visited'] for v in self.queue_data[queue_name]['visits']])
            avg_queue_time = np.mean(self.queue_data[queue_name]['queue_times']) if self.queue_data[queue_name]['queue_times'] else 0
            avg_exec_time = np.mean(self.queue_data[queue_name]['execution_times']) if self.queue_data[queue_name]['execution_times'] else 0
            
            summary_data.append([
                queue_name,
                f"{total_visits:,}",
                f"{avg_queue_time:.2f}",
                f"{avg_exec_time:.2f}"
            ])
        
        table = ax4.table(cellText=summary_data, 
                         colLabels=['Coda', 'Visite Tot.', 'Attesa Media', 'Exec Media'],
                         cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        ax4.set_title('Statistiche Riassuntive')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/confronto_code_ottimizzato.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Funzione principale ottimizzata per grandi dataset"""
    stats_file = "daily_stats.json"
    
    print("=== ANALIZZATORE OTTIMIZZATO PER GRANDI DATASET ===")
    print(f"Caricamento dati da: {stats_file}")
    
    try:
        # Crea analyzer con chunk size ottimizzato
        analyzer = LargeDatasetAnalyzer(stats_file, chunk_size=500)
        
        # Esegui analisi completa
        output_dir = analyzer.create_comprehensive_analysis()
        
        print(f"\n=== ANALISI COMPLETATA ===")
        print(f"Code analizzate: {len(analyzer.queue_data)}")
        print(f"Giorni simulati: {len(analyzer.daily_summaries)}")
        print(f"Grafici salvati in: {output_dir}/")
        
        # Statistiche di memoria
        total_events = sum(len(data['queue_times']) for data in analyzer.queue_data.values())
        print(f"Eventi processati (campionati): {total_events:,}")
        
        # Lista file generati
        print(f"\n=== NUOVI FILE GENERATI ===")
        print(f"- {output_dir}/analisi_temporale_sistema.png")
        print(f"- {output_dir}/heatmap_performance_code.png") 
        print(f"- {output_dir}/trend_temporali.png")
        print(f"- {output_dir}/confronto_code_ottimizzato.png")
        
        for queue_name in analyzer.queue_data.keys():
            print(f"- {output_dir}/analisi_{queue_name.lower()}.png")
        
    except FileNotFoundError:
        print(f"Errore: File {stats_file} non trovato!")
    except Exception as e:
        print(f"Errore durante l'analisi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
