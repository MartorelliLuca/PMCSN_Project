import json
import os

input_file = 'daily_stats.json'
output_folder = 'queue_means_dat'
os.makedirs(output_folder, exist_ok=True)

# This script expects daily_stats.json to be in json-lines format, one object per line
services = {}
with open(input_file, 'r') as f:
    for line in f:
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get('type') == 'daily_summary':
            stats = entry.get('stats', {})
            for service, service_stats in stats.items():
                # Each service, each day
                queue_time = service_stats.get('queue_time')
                date = entry.get('date')
                if service not in services:
                    services[service] = []
                services[service].append(queue_time)

# Write each service's daily mean queue time to a .dat file
for service, means in services.items():
    out_path = os.path.join(output_folder, f'{service}.dat')
    with open(out_path, 'w') as out_file:
        for mean in means:
            out_file.write(f'{mean}\n')
print(f'Exported mean queue times to {output_folder}/')
