"""
NetworkIQ — Classical OR Baseline Solver (MILP)
================================================
Implements the mathematical baseline using Google OR-Tools.
Objective: min Σ(Holding + Transfer + Lost-Sales Penalty)
Subject to: inventory balance, capacity, non-negativity constraints.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional

try:
    from ortools.linear_solver import pywraplp
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False


class BaselineSolver:
    """
    MILP-based inventory placement and transfer optimizer.
    Used as the classical benchmark against the AI multi-agent system.
    """

    def __init__(self, config: dict):
        self.config = config
        opt = config.get("optimization", {})
        self.holding_rate = opt.get("holding_cost_rate", 0.02)
        self.penalty_mult = opt.get("lost_sale_penalty_multiplier", 2.5)
        self.horizon = opt.get("planning_horizon_weeks", 12)

    def solve(self, demand_by_region: Dict[str, float],
              current_inventory: Dict[str, float],
              capacity: Dict[str, dict],
              transfer_costs: Dict[Tuple[str, str], float],
              avg_price: float = 500.0) -> dict:
        """
        Solve the network inventory placement problem.

        Args:
            demand_by_region: {region: total_demand_over_horizon}
            current_inventory: {region: current_stock}
            capacity: {region: {"total_units": N}}
            transfer_costs: {(from, to): cost_per_unit}
            avg_price: average SKU price for cost calculations

        Returns:
            dict with optimal transfers, costs, and service metrics.
        """
        if not HAS_ORTOOLS:
            return self._fallback_heuristic(demand_by_region, current_inventory,
                                            capacity, transfer_costs, avg_price)

        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            solver = pywraplp.Solver.CreateSolver("GLOP")
        if not solver:
            return self._fallback_heuristic(demand_by_region, current_inventory,
                                            capacity, transfer_costs, avg_price)

        regions = list(demand_by_region.keys())
        holding_cost = self.holding_rate * avg_price

        # Decision variables
        # X[i,j] = units transferred from region i to region j
        X = {}
        for i in regions:
            for j in regions:
                if i != j:
                    max_transfer = current_inventory.get(i, 0) * 0.4
                    X[i, j] = solver.NumVar(0, max_transfer, f"X_{i}_{j}")

        # S[i] = shortage (lost sales) at region i
        S = {}
        for i in regions:
            S[i] = solver.NumVar(0, solver.infinity(), f"S_{i}")

        # Inventory balance: final_inv = current + inflows - outflows
        # demand = final_inv + shortage => shortage = demand - final_inv (if positive)
        for i in regions:
            inflow = sum(X[j, i] for j in regions if j != i)
            outflow = sum(X[i, j] for j in regions if j != i)
            final_inv = current_inventory.get(i, 0) + inflow - outflow
            demand = demand_by_region.get(i, 0)
            # S[i] >= demand - final_inv
            solver.Add(S[i] >= demand - final_inv)

        # Capacity constraint
        for i in regions:
            inflow = sum(X[j, i] for j in regions if j != i)
            outflow = sum(X[i, j] for j in regions if j != i)
            final_inv = current_inventory.get(i, 0) + inflow - outflow
            cap = capacity.get(i, {}).get("total_units", 99999)
            solver.Add(final_inv <= cap)

        # Objective: minimize holding + transfer + penalty
        objective = solver.Objective()
        for i in regions:
            for j in regions:
                if i != j:
                    tc = transfer_costs.get((i, j), 100)
                    objective.SetCoefficient(X[i, j], tc)
            penalty = self.penalty_mult * avg_price
            objective.SetCoefficient(S[i], penalty)
        objective.SetMinimization()

        status = solver.Solve()

        if status == pywraplp.Solver.OPTIMAL:
            transfers = []
            total_transfer_cost = 0
            for i in regions:
                for j in regions:
                    if i != j and X[i, j].solution_value() > 0.5:
                        qty = round(X[i, j].solution_value())
                        tc = transfer_costs.get((i, j), 100) * qty
                        transfers.append({
                            "from": i, "to": j, "quantity": qty,
                            "transfer_cost": round(tc, 2)
                        })
                        total_transfer_cost += tc

            total_shortage = sum(S[i].solution_value() for i in regions)
            total_demand = sum(demand_by_region.values())
            service_level = 1 - (total_shortage / total_demand) if total_demand > 0 else 1.0

            total_inv = sum(current_inventory.values())
            holding = total_inv * holding_cost * self.horizon
            penalty_cost = total_shortage * self.penalty_mult * avg_price

            return {
                "status": "optimal",
                "transfers": transfers,
                "total_transfer_cost": round(total_transfer_cost, 2),
                "total_holding_cost": round(holding, 2),
                "total_penalty_cost": round(penalty_cost, 2),
                "total_cost": round(total_transfer_cost + holding + penalty_cost, 2),
                "service_level": round(service_level, 4),
                "total_shortage": round(total_shortage, 2),
                "solver": "MILP (OR-Tools)",
            }
        else:
            return {"status": "infeasible", "solver": "MILP (OR-Tools)", "transfers": []}

    def _fallback_heuristic(self, demand_by_region, current_inventory,
                            capacity, transfer_costs, avg_price):
        """Simple heuristic when OR-Tools is unavailable."""
        regions = list(demand_by_region.keys())
        surplus, deficit = {}, {}
        for r in regions:
            diff = current_inventory.get(r, 0) - demand_by_region.get(r, 0)
            if diff > 0:
                surplus[r] = diff
            elif diff < 0:
                deficit[r] = abs(diff)

        transfers = []
        total_tc = 0
        for def_r, need in sorted(deficit.items(), key=lambda x: -x[1]):
            for sur_r, avail in sorted(surplus.items(), key=lambda x: -x[1]):
                if avail <= 0 or need <= 0:
                    continue
                qty = min(need, avail)
                tc_unit = transfer_costs.get((sur_r, def_r), 100)
                tc = tc_unit * qty
                transfers.append({"from": sur_r, "to": def_r, "quantity": round(qty),
                                  "transfer_cost": round(tc, 2)})
                total_tc += tc
                surplus[sur_r] -= qty
                need -= qty
            deficit[def_r] = need

        total_shortage = sum(deficit.values())
        total_demand = sum(demand_by_region.values())
        sl = 1 - (total_shortage / total_demand) if total_demand > 0 else 1.0
        total_inv = sum(current_inventory.values())
        holding = total_inv * self.holding_rate * avg_price * self.horizon

        return {
            "status": "heuristic",
            "transfers": transfers,
            "total_transfer_cost": round(total_tc, 2),
            "total_holding_cost": round(holding, 2),
            "total_penalty_cost": round(total_shortage * self.penalty_mult * avg_price, 2),
            "total_cost": round(total_tc + holding + total_shortage * self.penalty_mult * avg_price, 2),
            "service_level": round(sl, 4),
            "total_shortage": round(total_shortage, 2),
            "solver": "Heuristic (fallback)",
        }
