
import json
import os
from datetime import datetime


mus={
    "InValutazione": (1/66250 )*160*70,
    "CompcompilazionePrecompilatailazioneC": 8/30,
    "InvioDiretto":1/3,
    "Instradamento":3 *3,
    "Autenticazione":2.252*4
}
def extract_visits_data(json_file_path):
    """
    Extract visits data from the JSON file and organize by service.
    
    Args:
        json_file_path (str): Path to the finito.json file
        
    Returns:
        dict: Dictionary with service names as keys and list of (date, visited) tuples as values
    """
    visits_by_service = {}
    
    try:
        with open(json_file_path, 'r') as file:
            for line in file:
                try:
                    data = json.loads(line.strip())
                    
                    # Only process daily_summary entries
                    if data.get('type') == 'daily_summary':
                        date = data.get('date')
                        stats = data.get('stats', {})
                        for service_name, service_data in stats.items():
                            visited = service_data.get('visited', 0)
                            if service_name not in visits_by_service:
                                visits_by_service[service_name] = []
                                visits_by_service[service_name].append({
                                'date': date,
                                'rho': visited/(24*60*60 * mus.get(service_name,1))
                            })
                            
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON line: {e}")
                    continue
                    
    except FileNotFoundError:
        print(f"File not found: {json_file_path}")
        return {}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}
    for service_name in visits_by_service:
        visits_by_service[service_name].sort(key=lambda x: x['date'])
    
    return visits_by_service



def save_to_json(visits_data, output_path):
    """
    Save the visits data to a JSON file.
    
    Args:
        visits_data (dict): Dictionary containing visits data by service
        output_path (str): Path to save the output JSON file
    """
    try:
        with open(output_path, 'w') as file:
            json.dump(visits_data, file, indent=2)
        print(f"\nData saved to: {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")


def main():
    # Define file paths
    input_file = "/home/alex/Desktop/pmProject/PMCSN_Project/src/transient_analysis_json/fint_n/finito.json"
    output_file = "/home/alex/Desktop/pmProject/PMCSN_Project/src/visits_by_service.json"
    
    print("Extracting visits data from finito.json...")
    
    # Extract the data
    visits_data = extract_visits_data(input_file)
    
    if visits_data:
        # Print summary
       
        
        # Save to JSON file
        save_to_json(visits_data, output_file)
        
            
    else:
        print("No data extracted. Please check the file path and format.")


if __name__ == "__main__":
    main()
