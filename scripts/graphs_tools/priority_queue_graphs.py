import json
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict
import pandas as pd

def load_priority_stats_data(filename):
    """Load data from priority queue simulation results, removing last 40 lines if present."""
    data = []
    with open(filename, 'r') as f:
        lines = [line for line in f if line.strip()]
        # Remove last 40 lines for transient analysis if file is long enough
        for line in lines:
            data.append(json.loads(line))
    return data

def extract_priority_queue_data(data):
    """Extract queue data handling both simple queues and priority sub-queues."""
    queue_data = defaultdict(lambda: {
        'queue_times': [],
        'execution_times': [],
        'queue_lengths': [],
        'response_times': [],
        'visits': []
    })

    for entry in data:
        if entry['type'] != 'daily_summary':
            continue

        stats = entry['stats']
        for queue_name, queue_stats in stats.items():
            if 'data' in queue_stats:
                # Handle shared data structure (aggregated across all sub-queues)
                qt = queue_stats['data']['queue_time']
                et = queue_stats['data']['executing_time']
                ql = queue_stats['data']['queue_lenght']
                rt = [q + e for q, e in zip(qt, et)] if qt and et and len(qt) == len(et) else []

                queue_data[queue_name]['queue_times'].extend(qt)
                queue_data[queue_name]['execution_times'].extend(et)
                queue_data[queue_name]['queue_lengths'].extend(ql)
                queue_data[queue_name]['response_times'].extend(rt)

                # Handle visits - check if it's dict (sub-queues) or int (single queue)
                if isinstance(queue_stats['visited'], dict):
                    # Sum all sub-queue visits
                    total_visits = sum(queue_stats['visited'].values())
                    queue_data[queue_name]['visits'].append(total_visits)
                    
                    # Also create separate entries for each sub-queue stats
                    for sub_queue, visit_count in queue_stats['visited'].items():
                        sub_queue_key = f"{queue_name}_{sub_queue}"
                        queue_data[sub_queue_key]['visits'].append(visit_count)
                        # Sub-queue specific averages
                        if sub_queue in queue_stats['queue_time']:
                            queue_data[sub_queue_key]['queue_times'].append(queue_stats['queue_time'][sub_queue])
                        if sub_queue in queue_stats['executing_time']:
                            queue_data[sub_queue_key]['execution_times'].append(queue_stats['executing_time'][sub_queue])
                        if sub_queue in queue_stats['queue_lenght']:
                            queue_data[sub_queue_key]['queue_lengths'].append(queue_stats['queue_lenght'][sub_queue])
                        
                        # Calculate response time for sub-queue
                        if (sub_queue in queue_stats['queue_time'] and 
                            sub_queue in queue_stats['executing_time']):
                            resp_time = queue_stats['queue_time'][sub_queue] + queue_stats['executing_time'][sub_queue]
                            queue_data[sub_queue_key]['response_times'].append(resp_time)
                else:
                    # Single queue
                    queue_data[queue_name]['visits'].append(queue_stats['visited'])

    return queue_data

def apply_priority_log_scale(ax, values, queue_name):
    """Apply log scale for priority queues, especially InValutazione."""
    if not values:
        return
    #if "InValutazione" in queue_name:
        #ax.set_yscale("log")
            # Light priority queue or general

# Replica seeds mapping
REPLICA_SEEDS = {
    "daily_stats_rep0.json": 123456789,
    "daily_stats_rep1.json": 1049824841,
    "daily_stats_rep2.json": 1343573286,
    "daily_stats_rep3.json": 1455055805,
    "daily_stats_rep4.json": 161222322,
    "daily_stats_rep5.json": 151721053,
    "daily_stats_rep6.json": 752455240,
}

def sort_legend(ax):
    """Sort legend by replica number."""
    handles, labels = ax.get_legend_handles_labels()
    def key(label):
        for part in label.split():
            if "rep" in part:
                try:
                    return int(part.replace("daily_stats_rep", "").replace(".json", ""))
                except ValueError:
                    pass
        return 999
    sorted_items = sorted(zip(handles, labels), key=lambda x: key(x[1]))
    ax.legend(*zip(*sorted_items))

def plot_priority_queue_comparison(queue_name, replica_data, output_dir, replica_seeds):
    """Create comparison chart for priority queues."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title(f"{queue_name} - Confronto tra repliche")
    ax.set_xlabel("Replica")
    ax.set_ylabel("Valore Medio")
    
    means = [(rep, np.mean(times)) for rep, times in replica_data.items() if times]
    means.sort()
    if not means:
        return
        
    labels, values = zip(*means)
    bar_labels = [f"{label}\n(seed={replica_seeds.get(label, 'N/A')})" for label in labels]
    
    bars = ax.bar(bar_labels, values, color='skyblue', alpha=0.7)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2f}',
                ha='center', va='bottom')
    
    apply_priority_log_scale(ax, values, queue_name)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/confronto_{queue_name.lower().replace('_', '_')}.png", dpi=300)
    plt.close()

def plot_priority_response_times(queue_name, queue_times, exec_times, output_dir, replica_seeds):
    """Plot response times for priority queues."""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_title(f"{queue_name} - Tempi di Risposta nel Tempo")
    ax.set_xlabel("Evento #")
    ax.set_ylabel("Tempo di Risposta (s)")
    
    all_vals = []
    for label in sorted(queue_times.keys()):
        q_times = queue_times[label]
        e_times = exec_times[label]
        
        if len(q_times) < 10 or len(e_times) < 10:
            continue
            
        # Calculate response times
        response_times = [q + e for q, e in zip(q_times, e_times)]
        moving_avg = pd.Series(response_times).rolling(window=min(100, len(response_times)//10), min_periods=1).mean()
        
        ax.plot(moving_avg, linewidth=1.2, alpha=0.7)  # Remove replica labels
        all_vals.extend(response_times)
    
    if all_vals:
        # Calculate mean of last 15000 events or all if less
        last_vals = all_vals[-15000:] if len(all_vals) > 15000 else all_vals
        mean_val = np.mean(last_vals)
        ax.axhline(mean_val, color='red', linestyle='--', 
                  label=f"Mean: {mean_val:.2f}", linewidth=2)
    
    apply_priority_log_scale(ax, all_vals, queue_name)
    ax.grid(True, alpha=0.3)
    ax.legend()  # Only shows mean now
    plt.tight_layout()
    plt.savefig(f"{output_dir}/tempi_risposta_{queue_name.lower().replace('_', '_')}.jpg", dpi=150, bbox_inches='tight')
    plt.close()

def plot_priority_visits(queue_name, visits_data, output_dir, replica_seeds):
    """Plot number of visits over time for priority queues."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_title(f"{queue_name} - Numero di Visite nel Tempo")
    ax.set_xlabel("Giorno")
    ax.set_ylabel("Numero di Visite")
    
    for label in sorted(visits_data.keys()):
        visits = visits_data[label]
        if len(visits) < 2:
            continue
            
        seed = replica_seeds.get(label, "N/A")
        ax.plot(visits, label=f"{label} (seed={seed})", linewidth=1.5, marker='o', markersize=3)
    
    ax.grid(True, alpha=0.3)
    sort_legend(ax)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/visite_{queue_name.lower().replace('_', '_')}.png", dpi=300)
    plt.close()

def plot_priority_queue_comprehensive(queue_name, queue_data, output_dir, replica_seeds):
    """Create comprehensive plot with 3 subplots: queue times, execution times, response times."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle(f"{queue_name} - Analisi Completa", fontsize=16, fontweight='bold')
    
    # Queue Times
    axes[0].set_title("Tempi di Attesa in Coda")
    axes[0].set_xlabel("Evento #")
    axes[0].set_ylabel("Tempo di Attesa (s)")
    
    queue_all_vals = []
    for label in sorted(queue_data.keys()):
        q_times = queue_data[label]['queue_times']
        if len(q_times) < 10:
            continue
        moving_avg = pd.Series(q_times).rolling(window=max(10, len(q_times)//50), min_periods=1).mean()
        axes[0].plot(moving_avg, linewidth=1.0, alpha=0.7)  # Remove replica labels
        queue_all_vals.extend(q_times)
    
    if queue_all_vals:
        mean_queue = np.mean(queue_all_vals)
        axes[0].axhline(mean_queue, color='red', linestyle='--', label=f"Mean: {mean_queue:.2f}", linewidth=1)
    
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()  # Only shows mean
    
    # Execution Times
    axes[1].set_title("Tempi di Esecuzione")
    axes[1].set_xlabel("Evento #")
    axes[1].set_ylabel("Tempo di Esecuzione (s)")
    
    exec_all_vals = []
    for label in sorted(queue_data.keys()):
        e_times = queue_data[label]['execution_times']
        if len(e_times) < 10:
            continue
        moving_avg = pd.Series(e_times).rolling(window=max(10, len(e_times)//50), min_periods=1).mean()
        axes[1].plot(moving_avg, linewidth=1.0, alpha=0.7)  # Remove replica labels
        exec_all_vals.extend(e_times)
    
    if exec_all_vals:
        mean_exec = np.mean(exec_all_vals)
        axes[1].axhline(mean_exec, color='red', linestyle='--', label=f"Mean: {mean_exec:.2f}", linewidth=1)
    
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()  # Only shows mean
    
    # Response Times
    axes[2].set_title("Tempi di Risposta Totali")
    axes[2].set_xlabel("Evento #")
    axes[2].set_ylabel("Tempo di Risposta (s)")
    
    resp_all_vals = []
    for label in sorted(queue_data.keys()):
        r_times = queue_data[label]['response_times']
        if len(r_times) < 10:
            continue
        moving_avg = pd.Series(r_times).rolling(window=max(10, len(r_times)//50), min_periods=1).mean()
        axes[2].plot(moving_avg, linewidth=1.0, alpha=0.7)  # Remove replica labels
        resp_all_vals.extend(r_times)
    
    if resp_all_vals:
        mean_resp = np.mean(resp_all_vals)
        axes[2].axhline(mean_resp, color='red', linestyle='--', label=f"Mean: {mean_resp:.2f}", linewidth=1)
    
    apply_priority_log_scale(axes[2], resp_all_vals, queue_name)
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()  # Only shows mean
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/completa_{queue_name.lower().replace('_', '_')}.jpg", dpi=150, bbox_inches='tight')
    plt.close()

def plot_invalutazione_weighted_daily_means(all_queue_data, output_dir):
    """Plot InValutazione using weighted daily means combining all sub-queues."""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_title("InValutazione - Tempi Medi Giornalieri (pesati per visite - tutte le code)")
    ax.set_xlabel("Giorno")
    ax.set_ylabel("Tempo Medio Pesato (s)")
    
    # Find all InValutazione queues (main + sub-queues)
    invalutazione_queues = {}
    for queue_name, queue_replicas in all_queue_data.items():
        if "InValutazione" in queue_name:
            invalutazione_queues[queue_name] = queue_replicas
    
    if not invalutazione_queues:
        print("No InValutazione queues found")
        return
    
    all_daily_weighted = []
    # Variables for calculating the true weighted mean
    total_weighted_sum = 0
    total_visits = 0
    
    # Process each replica
    for replica_idx in range(len(list(invalutazione_queues.values())[0].keys())):
        replica_files = list(list(invalutazione_queues.values())[0].keys())
        if replica_idx >= len(replica_files):
            continue
            
        replica_file = replica_files[replica_idx]
        
        # Get the maximum number of days across all queues for this replica
        max_days = 0
        for queue_name, queue_replicas in invalutazione_queues.items():
            if replica_file in queue_replicas:
                replica_data = queue_replicas[replica_file]
                max_days = max(max_days, len(replica_data.get('visits', [])))
        
        # Calculate weighted daily means for this replica
        daily_weighted = []
        for day in range(max_days):
            day_weighted_sum = 0
            day_total_visits = 0
            
            # Sum across all InValutazione queues for this day
            for queue_name, queue_replicas in invalutazione_queues.items():
                if replica_file in queue_replicas:
                    replica_data = queue_replicas[replica_file]
                    
                    if (day < len(replica_data.get('queue_times', [])) and 
                        day < len(replica_data.get('visits', []))):
                        
                        queue_time = replica_data['queue_times'][day]
                        visits = replica_data['visits'][day]
                        
                        if visits > 0:
                            day_weighted_sum += queue_time * visits
                            day_total_visits += visits
                            # Add to global totals for correct weighted mean
                            total_weighted_sum += queue_time * visits
                            total_visits += visits
            
            # Calculate weighted average for this day
            if day_total_visits > 0:
                weighted_avg = day_weighted_sum / day_total_visits
                daily_weighted.append(weighted_avg)
            else:
                daily_weighted.append(0)
        
        if daily_weighted:
            ax.plot(daily_weighted, linewidth=1.2, alpha=0.7)
            all_daily_weighted.extend(daily_weighted)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/weighted_daily_invalutazione.jpg", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Created weighted daily InValutazione graph with {len(all_daily_weighted)} data points")

def create_priority_summary_report(all_data, output_dir):
    """Create a summary report for all priority queues."""
    report_path = f"{output_dir}/priority_analysis_summary.txt"
    
    with open(report_path, 'w') as f:
        f.write("PRIORITY QUEUE ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        for queue_name, queue_data in all_data.items():
            f.write(f"{queue_name}:\n")
            f.write("-" * 30 + "\n")
            
            # Calculate statistics
            if queue_data['queue_times']:
                avg_queue_time = np.mean(queue_data['queue_times'])
                f.write(f"  Avg Queue Time: {avg_queue_time:.4f}s\n")
            
            if queue_data['execution_times']:
                avg_exec_time = np.mean(queue_data['execution_times'])
                f.write(f"  Avg Execution Time: {avg_exec_time:.4f}s\n")
            
            if queue_data['response_times']:
                avg_response_time = np.mean(queue_data['response_times'])
                f.write(f"  Avg Response Time: {avg_response_time:.4f}s\n")
            
            if queue_data['visits']:
                total_visits = sum(queue_data['visits'])
                avg_visits = np.mean(queue_data['visits'])
                f.write(f"  Total Visits: {total_visits}\n")
                f.write(f"  Avg Daily Visits: {avg_visits:.2f}\n")
            
            f.write("\n")
    
    print(f"✅ Summary report saved to {report_path}")

def analyze_priority_queue_directory(transient_dir="transient_analysis_json", output_dir="graphs/priority_queues"):
    """Main analysis function for priority queue simulation results."""
    if not os.path.exists(transient_dir):
        print(f"Directory {transient_dir}/ non trovata.")
        return

    json_files = [f for f in os.listdir(transient_dir)
                  if f.startswith("daily_stats_rep") and f.endswith(".json")]
    if not json_files:
        print(f"Nessun file daily_stats_rep*.json trovato in {transient_dir}/")
        return

    print(f"\n📊 Analisi code prioritarie: trovati {len(json_files)} file in {transient_dir}/")

    all_queue_data = defaultdict(lambda: defaultdict(lambda: {
        'queue_times': [],
        'execution_times': [],
        'queue_lengths': [],
        'response_times': [],
        'visits': []
    }))

    # Load and process all files
    for file in json_files:
        path = os.path.join(transient_dir, file)
        fname = os.path.basename(file)
        print(f"  Caricamento {fname} ...")
        data = load_priority_stats_data(path)
        queue_data = extract_priority_queue_data(data)

        for queue_name, q_data in queue_data.items():
            all_queue_data[queue_name][fname] = q_data

    os.makedirs(output_dir, exist_ok=True)

    # Generate plots for each queue
    invalutazione_processed = False
    for queue_name in all_queue_data:
        print(f"\n🔍 Analisi per la coda: {queue_name}")
        
        # Extract data for plotting
        queue_times_by_replica = {replica: data['queue_times'] 
                                 for replica, data in all_queue_data[queue_name].items()}
        exec_times_by_replica = {replica: data['execution_times'] 
                               for replica, data in all_queue_data[queue_name].items()}
        
        # Generate plots (removed confronto and visits)
        if (queue_times_by_replica and exec_times_by_replica and 
            any(queue_times_by_replica.values()) and any(exec_times_by_replica.values())):
            plot_priority_response_times(queue_name, queue_times_by_replica, exec_times_by_replica, output_dir, REPLICA_SEEDS)
        
        plot_priority_queue_comprehensive(queue_name, all_queue_data[queue_name], output_dir, REPLICA_SEEDS)
    
    # Create single weighted graph for all InValutazione queues
    plot_invalutazione_weighted_daily_means(all_queue_data, output_dir)

    # Create summary report
    summary_data = {}
    for queue_name in all_queue_data:
        # Aggregate data across replicas
        combined_data = {
            'queue_times': [],
            'execution_times': [],
            'response_times': [],
            'visits': []
        }
        for replica_data in all_queue_data[queue_name].values():
            combined_data['queue_times'].extend(replica_data['queue_times'])
            combined_data['execution_times'].extend(replica_data['execution_times'])
            combined_data['response_times'].extend(replica_data['response_times'])
            combined_data['visits'].extend(replica_data['visits'])
        summary_data[queue_name] = combined_data

    create_priority_summary_report(summary_data, output_dir)
    
    print(f"\n✅ Analisi code prioritarie completata! Grafici salvati in: {output_dir}/")
    print(f"📂 File generati:")
    for queue_name in all_queue_data:
        safe_name = queue_name.lower().replace('_', '_')
        print(f"   - tempi_risposta_{safe_name}.jpg")
        print(f"   - completa_{safe_name}.jpg")
    print(f"   - weighted_daily_invalutazione.jpg  (combined all InValutazione queues)")
    print(f"   - priority_analysis_summary.txt")

if __name__ == "__main__":
    analyze_priority_queue_directory()
