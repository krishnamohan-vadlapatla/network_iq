"""
Run Optimizer Script
====================
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_loader import prepare_full_dataset
from agents.orchestrator_agent import OrchestratorAgent

def main():
    print("Loading data...")
    try:
        data = prepare_full_dataset()
    except Exception as e:
        print(f"Error loading data: {e}. Please ensure data/indian_store_data.csv exists.")
        return
        
    print("Starting Orchestrator Agent...")
    orchestrator = OrchestratorAgent(data["config"])
    
    result = orchestrator.run_optimization_cycle(data)
    
    if result["status"] == "success":
        print("Optimization complete!")
        print(f"Generated {len(result['transfers'])} transfers.")
        print(f"Pending approval: {len(result['pending_approval'])}")
        print(f"Total Decision Cost: INR {result['total_decision_cost']}")
    else:
        print("Optimization failed.")

if __name__ == "__main__":
    main()
