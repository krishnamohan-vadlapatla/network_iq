"""
NetworkIQ — Benchmark Runner
==============================
Compares AI-driven multi-agent optimization against classical OR-Tools baseline.
Simulates demand shocks and evaluates robustness.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from baseline_solver import BaselineSolver
from agents.orchestrator_agent import OrchestratorAgent
import benchmarks.metrics as mx


class BenchmarkRunner:
    def __init__(self, config: dict, data: dict):
        self.config = config
        self.data = data
        self.baseline = BaselineSolver(config)
        self.orchestrator = OrchestratorAgent(config)
        
        opt = config.get("optimization", {})
        self.horizon = opt.get("planning_horizon_weeks", 12)
        self.holding_rate = opt.get("holding_cost_rate", 0.02)
        self.penalty_mult = opt.get("lost_sale_penalty_multiplier", 2.5)
        
        bench = config.get("benchmark", {})
        self.shock_prob = bench.get("demand_shock_probability", 0.15)
        self.shock_mag = bench.get("demand_shock_magnitude", 0.50)
        self.num_sims = bench.get("num_simulations", 3)
        self.seed = config.get("random_seed", 42)

    def run_benchmark(self):
        """Run comparisons across strategies."""
        print(f"Running benchmark with {self.num_sims} simulations...")
        
        results = []
        
        # 1. Base case (no shocks)
        base_or = self._run_or_baseline(self.data)
        base_ai = self._run_ai_agents(self.data)
        
        results.append(self._format_result("OR-Only", "Base", base_or))
        results.append(self._format_result("AI-Agents", "Base", base_ai))
        
        # 2. Simulations with shocks
        rng = np.random.RandomState(self.seed)
        for i in range(self.num_sims):
            shocked_data = self._inject_shocks(self.data, rng)
            
            sim_or = self._run_or_baseline(shocked_data)
            sim_ai = self._run_ai_agents(shocked_data)
            
            results.append(self._format_result("OR-Only", f"Shock_{i+1}", sim_or))
            results.append(self._format_result("AI-Agents", f"Shock_{i+1}", sim_ai))
            
        df = pd.DataFrame(results)
        
        # Aggregate
        summary = df.groupby("Strategy").agg({
            "Service_Level": "mean",
            "Total_Cost": "mean",
            "In_Stock_Rate": "mean",
            "Decision_Cost": "mean"
        }).reset_index()
        
        return {"raw_results": df, "summary": summary}

    def _run_or_baseline(self, data: dict) -> dict:
        """Run classical MILP solver."""
        # Aggregate demand by region
        wd = data["weekly_demand"]
        dem_by_region = wd.groupby("Region")["Weekly_Demand"].sum().to_dict()
        
        # Aggregate inventory
        ci = data["current_inventory"]
        if "Current_Stock" in ci.columns:
            inv_by_region = ci.groupby("Region")["Current_Stock"].sum().to_dict()
        else:
            inv_by_region = {r: 0 for r in data["regions"]}
            
        avg_price = data["sku_summary"]["Avg_Price"].mean() if not data["sku_summary"].empty else 500
            
        res = self.baseline.solve(
            dem_by_region, inv_by_region, data["capacity"], 
            data["transfer_costs"], avg_price
        )
        
        return {
            "Total_Cost": res.get("total_cost", 0),
            "Service_Level": res.get("service_level", 0.0),
            "In_Stock_Rate": res.get("service_level", 0.0), # Approx for OR
            "Decision_Cost": 0.10  # Cheap OR compute
        }

    def _run_ai_agents(self, data: dict) -> dict:
        """Run multi-agent system."""
        res = self.orchestrator.run_optimization_cycle(data)
        metrics = res.get("metrics", {})
        
        return {
            "Total_Cost": metrics.get("total_transfer_cost", 0) * 2, # simplified total cost proxy
            "Service_Level": metrics.get("service_level", 0.0),
            "In_Stock_Rate": metrics.get("a_class_instock_rate", 0.0),
            "Decision_Cost": res.get("total_decision_cost", 0.0)
        }
        
    def _inject_shocks(self, data: dict, rng) -> dict:
        """Inject random demand shocks."""
        import copy
        shocked = copy.deepcopy(data)
        wd = shocked["weekly_demand"].copy()
        
        # Apply shocks
        mask = rng.rand(len(wd)) < self.shock_prob
        multipliers = 1.0 + rng.uniform(-self.shock_mag, self.shock_mag, size=len(wd))
        
        wd.loc[mask, "Weekly_Demand"] = (wd.loc[mask, "Weekly_Demand"] * multipliers[mask]).astype(int)
        shocked["weekly_demand"] = wd
        
        return shocked

    def _format_result(self, strategy: str, scenario: str, res: dict) -> dict:
        return {
            "Strategy": strategy,
            "Scenario": scenario,
            "Service_Level": res["Service_Level"],
            "Total_Cost": res["Total_Cost"],
            "In_Stock_Rate": res["In_Stock_Rate"],
            "Decision_Cost": res["Decision_Cost"]
        }


if __name__ == "__main__":
    from data_loader import prepare_full_dataset
    data = prepare_full_dataset()
    runner = BenchmarkRunner(data["config"], data)
    results = runner.run_benchmark()
    print("\nBenchmark Summary:")
    print(results["summary"].to_markdown(index=False))
