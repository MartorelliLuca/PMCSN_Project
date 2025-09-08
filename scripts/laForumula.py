from math import sqrt
import json
import matplotlib.pyplot as plt
import numpy as np
import os
from desPython import rvms

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
stats=read_daily_stats("transient_analysis_json/daily_stats_rep0.json")
centers=["InValutazione"]
centersData={center:{
"exited":[],
"queue_time": [],
"executing_time": [],
"total_visits": []  # Track total visits across all sub-queues
} for center in centers}

for row in stats:
    # Check if row has "stats" key
    if "stats" not in row:
        print("Warning: No 'stats' key in this row, skipping...")
        continue
    output= row["summary"]["usciti"]
    row_stats = row["stats"]
    # Check if all centers exist in stats
    all_centers_present = all(center in row_stats.keys() for center in centers)
    if(not all_centers_present):
        break
    
    for center in centers:
        if all_centers_present:  # Only process if center exists
            centersData[center]["exited"].append(output)
            
            # Handle new InValutazione structure with sub-queues
            if center == "InValutazione":
                # Extract data from the three sub-queues
                sub_queues = row_stats[center]["visited"]  # {"Leggera": X, "Diretta": Y, "Pesante": Z}
                queue_times = row_stats[center]["queue_time"]  # {"Leggera": X, "Diretta": Y, "Pesante": Z}
                exec_times = row_stats[center]["executing_time"]  # {"Leggera": X, "Diretta": Y, "Pesante": Z}
                
                # Calculate weighted average queue time across all sub-queues
                total_weighted_queue_time = 0
                total_visits = 0
                total_weighted_exec_time = 0
                
                for sub_queue_name in sub_queues:
                    visits = sub_queues[sub_queue_name]
                    queue_time = queue_times[sub_queue_name]
                    exec_time = exec_times[sub_queue_name]
                    
                    total_weighted_queue_time += queue_time * visits
                    total_weighted_exec_time += exec_time * visits
                    total_visits += visits
                
                # Calculate weighted averages
                if total_visits > 0:
                    weighted_avg_queue_time = total_weighted_queue_time / total_visits
                    weighted_avg_exec_time = total_weighted_exec_time / total_visits
                else:
                    weighted_avg_queue_time = 0
                    weighted_avg_exec_time = 0
                
                centersData[center]["queue_time"].append(weighted_avg_queue_time)
                centersData[center]["executing_time"].append(weighted_avg_exec_time)
                centersData[center]["total_visits"].append(total_visits)
            else:
                # Handle other centers with the old structure
                centersData[center]["queue_time"].append(row_stats[center]["queue_time"])
                centersData[center]["executing_time"].append(row_stats[center]["executing_time"])
        else:
            print(f"Warning: {center} not found in stats")

print(f"Debug - First few days of InValutazione:")
print(f"Queue times: {centersData['InValutazione']['queue_time'][:5]}")
print(f"Total visits: {centersData['InValutazione']['total_visits'][:5]}")
print(f"Exited: {centersData['InValutazione']['exited'][:5]}")

def calculate_user_stress_score(queue_times, exited_counts):
    """
    Calculate a normalized user stress score between 1-100.
    
    Args:
        queue_times: List of daily average wait times (seconds)
        exited_counts: List of daily exit counts (throughput)
    
    Returns:
        Float: Normalized stress score (1-100, where 1=best, 100=worst)
    """
    if not queue_times or not exited_counts:
        return 1
    
    # Convert to numpy arrays
    wait_times = np.array(queue_times)
    throughput = np.array(exited_counts)
    
    # Simple stress score: average wait time weighted by volume
    total_user_wait = np.sum(wait_times * throughput)
    total_users = np.sum(throughput)
    
    if total_users == 0:
        return 1
  
    raw_stress = total_user_wait / total_users
    

    
    max_acceptable_wait = 14*64*64*24 
    
    normalized_score = 1 + (raw_stress / max_acceptable_wait) * 99
    
    normalized_score = min(normalized_score, 100)
    
    return normalized_score

# Calculate stress score for InValutazione
stress_score = calculate_user_stress_score(
    centersData["InValutazione"]["queue_time"], 
    centersData["InValutazione"]["exited"]
)

print(f"\n📊 User Stress Score: {stress_score:.1f}/100")
print(f"   (1 = excellent, 100 = critical user experience)")

# Interpretation
if stress_score <= 10:
    interpretation = "🟢 EXCELLENT - Users very satisfied"
elif stress_score <= 25:
    interpretation = "🟡 GOOD - Acceptable user experience"
elif stress_score <= 50:
    interpretation = "🟠 MODERATE - Some user frustration expected"
elif stress_score <= 75:
    interpretation = "🔴 POOR - High user frustration"
else:
    interpretation = "⛔ CRITICAL - Users likely to abandon system"

print(f"   Status: {interpretation}")

