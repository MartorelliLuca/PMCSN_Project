#!/usr/bin/env python3
"""
Simulation Results Analyzer
Analyzes simulation_results.json and generates summary statistics.
"""

import json
import statistics
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime object."""
    return datetime.fromisoformat(timestamp_str)


def calculate_waiting_time(state: Dict) -> float:
    """Calculate waiting time in queue (service_start_time - enqueue_time)."""
    if state.get('service_start_time') and state.get('enqueue_time'):
        enqueue = parse_timestamp(state['enqueue_time'])
        start = parse_timestamp(state['service_start_time'])
        return (start - enqueue).total_seconds()
    return 0.0


def analyze_simulation_results(input_file: str, output_file: str = "simulation_analysis.json"):
    """
    Analyze simulation results and generate summary statistics.
    
    Args:
        input_file (str): Path to simulation_results.json
        output_file (str): Path to output analysis file
    """
    
    # Data structures to collect statistics
    entities = []
    service_stats = defaultdict(lambda: {
        'waiting_times': [],
        'service_times': [],
        'queue_lengths': [],
        'total_entities': 0,
        'total_time_in_system': []
    })
    
    total_simulation_times = []
    entity_count = 0
    
    print("📊 Analyzing simulation results...")
    
    # Read and parse the JSON Lines file
    parse_errors = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                if data.get('type') == 'entity':
                    entity_count += 1
                    entities.append(data)
                    total_simulation_times.append(data.get('total_simulation_time', 0))
                    
                    # Analyze each state in the entity's journey
                    for state in data.get('states', []):
                        service_name = state.get('service_name')
                        if service_name and service_name != 'EndBlock':  # Skip EndBlock
                            
                            # Waiting time (time in queue before service)
                            waiting_time = calculate_waiting_time(state)
                            service_stats[service_name]['waiting_times'].append(waiting_time)
                            
                            # Service time
                            service_time = state.get('service_duration_seconds', 0)
                            if service_time is not None:
                                service_stats[service_name]['service_times'].append(service_time)
                            
                            # Queue length when this entity entered
                            queue_length = state.get('queue_length', 0)
                            service_stats[service_name]['queue_lengths'].append(queue_length)
                            
                            # Total time in this service (waiting + service)
                            total_time = waiting_time + (service_time if service_time else 0)
                            service_stats[service_name]['total_time_in_system'].append(total_time)
                            
                            service_stats[service_name]['total_entities'] += 1
                    
                    # Progress indicator
                    if entity_count % 100 == 0:
                        print(f"  Processed {entity_count} entities...")
                        
            except json.JSONDecodeError as e:
                parse_errors += 1
                # Only show first few errors to avoid spam
                if parse_errors <= 5:
                    print(f"⚠️  Warning: Could not parse line {line_num}: {e}")
                    # Show the problematic line for debugging
                    print(f"     Line content: {repr(line[:100])}")
                elif parse_errors == 6:
                    print(f"⚠️  ... suppressing further parse errors (total so far: {parse_errors})")
                continue
    
    print(f"✅ Analysis complete: {entity_count} entities processed")
    if parse_errors > 0:
        print(f"⚠️  Total parse errors encountered: {parse_errors} lines (skipped)")
    
    # Calculate summary statistics
    analysis = {
        "analysis_timestamp": datetime.now().isoformat(),
        "input_file": input_file,
        "total_entities_analyzed": entity_count,
        "overall_statistics": {},
        "service_statistics": {},
        "system_performance": {}
    }
    
    # Overall system statistics
    if total_simulation_times:
        analysis["overall_statistics"] = {
            "mean_total_simulation_time": statistics.mean(total_simulation_times),
            "median_total_simulation_time": statistics.median(total_simulation_times),
            "min_total_simulation_time": min(total_simulation_times),
            "max_total_simulation_time": max(total_simulation_times),
            "std_total_simulation_time": statistics.stdev(total_simulation_times) if len(total_simulation_times) > 1 else 0
        }
    
    # Per-service statistics
    for service_name, stats in service_stats.items():
        service_analysis = {
            "total_entities_served": stats['total_entities'],
            "waiting_time_statistics": {},
            "service_time_statistics": {},
            "queue_statistics": {},
            "total_time_in_service_statistics": {}
        }
        
        # Waiting time statistics
        if stats['waiting_times']:
            service_analysis["waiting_time_statistics"] = {
                "mean_waiting_time": statistics.mean(stats['waiting_times']),
                "median_waiting_time": statistics.median(stats['waiting_times']),
                "min_waiting_time": min(stats['waiting_times']),
                "max_waiting_time": max(stats['waiting_times']),
                "std_waiting_time": statistics.stdev(stats['waiting_times']) if len(stats['waiting_times']) > 1 else 0,
                "total_entities_with_waiting": len([t for t in stats['waiting_times'] if t > 0])
            }
        
        # Service time statistics
        if stats['service_times']:
            service_analysis["service_time_statistics"] = {
                "mean_service_time": statistics.mean(stats['service_times']),
                "median_service_time": statistics.median(stats['service_times']),
                "min_service_time": min(stats['service_times']),
                "max_service_time": max(stats['service_times']),
                "std_service_time": statistics.stdev(stats['service_times']) if len(stats['service_times']) > 1 else 0
            }
        
        # Queue statistics
        if stats['queue_lengths']:
            queue_counter = Counter(stats['queue_lengths'])
            service_analysis["queue_statistics"] = {
                "mean_queue_length": statistics.mean(stats['queue_lengths']),
                "median_queue_length": statistics.median(stats['queue_lengths']),
                "min_queue_length": min(stats['queue_lengths']),
                "max_queue_length": max(stats['queue_lengths']),
                "queue_length_distribution": dict(queue_counter),
                "probability_empty_queue": queue_counter.get(0, 0) / len(stats['queue_lengths'])
            }
        
        # Total time in service (waiting + service)
        if stats['total_time_in_system']:
            service_analysis["total_time_in_service_statistics"] = {
                "mean_total_time": statistics.mean(stats['total_time_in_system']),
                "median_total_time": statistics.median(stats['total_time_in_system']),
                "min_total_time": min(stats['total_time_in_system']),
                "max_total_time": max(stats['total_time_in_system']),
                "std_total_time": statistics.stdev(stats['total_time_in_system']) if len(stats['total_time_in_system']) > 1 else 0
            }
        
        analysis["service_statistics"][service_name] = service_analysis
    
    # System performance metrics
    total_waiting_times = []
    total_service_times = []
    total_queue_lengths = []
    
    for stats in service_stats.values():
        total_waiting_times.extend(stats['waiting_times'])
        total_service_times.extend(stats['service_times'])
        total_queue_lengths.extend(stats['queue_lengths'])
    
    if total_waiting_times or total_service_times:
        analysis["system_performance"] = {
            "system_wide_metrics": {
                "total_services": len(service_stats),
                "average_waiting_time_across_all_services": statistics.mean(total_waiting_times) if total_waiting_times else 0,
                "average_service_time_across_all_services": statistics.mean(total_service_times) if total_service_times else 0,
                "average_queue_length_across_all_services": statistics.mean(total_queue_lengths) if total_queue_lengths else 0,
                "system_utilization_indicator": len([t for t in total_queue_lengths if t > 0]) / len(total_queue_lengths) if total_queue_lengths else 0
            }
        }
    
    # Write analysis to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Analysis saved to: {output_file}")
    
    # Print summary to console
    print("\n📈 SIMULATION ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Total entities analyzed: {entity_count}")
    if total_simulation_times:
        print(f"Mean simulation time: {statistics.mean(total_simulation_times):.2f} seconds")
    
    print(f"\nServices analyzed: {len(service_stats)}")
    for service_name, stats in service_stats.items():
        print(f"\n🔸 {service_name}:")
        print(f"  - Entities served: {stats['total_entities']}")
        if stats['waiting_times']:
            print(f"  - Mean waiting time: {statistics.mean(stats['waiting_times']):.2f}s")
        if stats['service_times']:
            print(f"  - Mean service time: {statistics.mean(stats['service_times']):.2f}s")
        if stats['total_time_in_system']:
            print(f"  - Mean time in system: {statistics.mean(stats['total_time_in_system']):.2f}s")
        if stats['queue_lengths']:
            print(f"  - Mean queue length: {statistics.mean(stats['queue_lengths']):.2f}")
    
    # Overall system metrics
    if total_waiting_times and total_service_times:
        all_system_times = []
        for stats in service_stats.values():
            all_system_times.extend(stats['total_time_in_system'])
        
        if all_system_times:
            print(f"\n🌐 OVERALL SYSTEM METRICS:")
            print(f"  - Mean user time in system (all services): {statistics.mean(all_system_times):.2f}s")
            print(f"  - Total system throughput: {entity_count} entities")
            if total_simulation_times:
                print(f"  - System efficiency: {entity_count / statistics.mean(total_simulation_times):.2f} entities/second")
    
    return analysis


if __name__ == "__main__":
    # Run the analysis
    try:
        analysis_results = analyze_simulation_results("simulation_results_fixed.json")
        print(f"\n✅ Analysis completed successfully!")
    except FileNotFoundError:
        print("❌ Error: simulation_results_fixed.json not found!")
        print("💡 Try running fix_json_format.py first to fix the JSON format")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
