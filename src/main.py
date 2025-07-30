

import sys
from simulation import SImulationEngine


def run_normal_mode(num_entities=10):
    """Run simulation in normal mode"""
    print(f"🚀 Running simulation in NORMAL mode with {num_entities} entities...")
    SImulationEngine.SimulationEngine().normal(num_entities)



def run_test_mode(num_entities=5):
    """Run simulation in test mode"""
    print(f"🧪 Running simulation in TEST mode with {num_entities} entities...")
    # You can modify parameters for testing (e.g., fewer entities, different config)
    SImulationEngine.SimulationEngine().test(num_entities)


if __name__ == "__main__":
    # Get command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "normal"
    
    # Get number of entities (second parameter)
    num_entities = None
    if len(sys.argv) > 2:
        try:
            num_entities = int(sys.argv[2])
            if num_entities <= 0:
                print("❌ Error: Number of entities must be a positive integer")
                sys.exit(1)
        except ValueError:
            print(f"❌ Error: '{sys.argv[2]}' is not a valid integer")
            print("💡 Usage: python main.py [normal|test] [number_of_entities]")
            sys.exit(1)
    
    # Case switch statement using match-case (Python 3.10+) or if-elif
    try:
        match mode.lower():
            case "normal":
                if num_entities is not None:
                    run_normal_mode(num_entities)
                else:
                    run_normal_mode()
            case "test":
                if num_entities is not None:
                    run_test_mode(num_entities)
                else:
                    run_test_mode()
            case _:
                print(f"❌ Error: Unknown mode '{mode}'")
                print("💡 Usage: python main.py [normal|test] [number_of_entities]")
                print("   - normal: Run full simulation")
                print("   - test: Run test simulation with reduced parameters")
                print("   - number_of_entities: Optional integer (default: normal=10, test=5)")
                sys.exit(1)
    except NameError:
        # Fallback for Python < 3.10 (using if-elif instead of match-case)
        if mode.lower() == "normal":
            if num_entities is not None:
                run_normal_mode(num_entities)
            else:
                run_normal_mode()
        elif mode.lower() == "test":
            if num_entities is not None:
                run_test_mode(num_entities)
            else:
                run_test_mode()
        else:
            print(f"❌ Error: Unknown mode '{mode}'")
            print("💡 Usage: python main.py [normal|test] [number_of_entities]")
            print("   - normal: Run full simulation")
            print("   - test: Run test simulation with reduced parameters")
            print("   - number_of_entities: Optional integer (default: normal=10, test=5)")
            sys.exit(1)
    
    print("✅ Simulation completed!")