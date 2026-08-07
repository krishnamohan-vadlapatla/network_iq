"""
Run Benchmark Script
====================
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from data_loader import prepare_full_dataset
from benchmarks.benchmark_runner import BenchmarkRunner

def main():
    print("Loading data...")
    try:
        data = prepare_full_dataset()
    except Exception as e:
        print(f"Error loading data: {e}. Please ensure data/indian_store_data.csv exists.")
        return
        
    print("Initializing Benchmark Runner...")
    runner = BenchmarkRunner(data["config"], data)
    
    results = runner.run_benchmark()
    
    print("\n=============================================")
    print(" BENCHMARK RESULTS (AI Agents vs Classical OR) ")
    print("=============================================\n")
    print(results["summary"].to_markdown(index=False))
    print("\nDone.")

if __name__ == "__main__":
    main()
