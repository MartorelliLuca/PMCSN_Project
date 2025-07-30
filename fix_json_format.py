#!/usr/bin/env python3
"""
Fix JSON Lines format by converting pretty-printed JSON back to single lines.
"""

import json
import re

def fix_json_lines_format(input_file: str, output_file: str):
    """
    Convert pretty-printed JSON back to JSON Lines format.
    """
    print(f"🔧 Fixing JSON Lines format from {input_file} to {output_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by closing braces that are on their own lines followed by opening braces
    # This pattern matches the end of one JSON object and start of the next
    json_objects = []
    current_object = ""
    brace_count = 0
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        current_object += line
        
        # Count braces to know when we have a complete JSON object
        brace_count += line.count('{') - line.count('}')
        
        if brace_count == 0 and current_object:
            # We have a complete JSON object
            try:
                # Parse and re-serialize to ensure it's valid JSON
                parsed = json.loads(current_object)
                json_objects.append(json.dumps(parsed, separators=(',', ':')))
                current_object = ""
            except json.JSONDecodeError:
                # If parsing fails, keep accumulating
                pass
    
    # Write the fixed JSON Lines format
    with open(output_file, 'w', encoding='utf-8') as f:
        for json_obj in json_objects:
            f.write(json_obj + '\n')
    
    print(f"✅ Fixed {len(json_objects)} JSON objects")
    return len(json_objects)

if __name__ == "__main__":
    # Fix the format
    count = fix_json_lines_format("simulation_results.json", "simulation_results_fixed.json")
    print(f"📁 Fixed file saved as: simulation_results_fixed.json")
