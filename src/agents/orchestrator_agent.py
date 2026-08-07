"""
NetworkIQ — Orchestrator Agent
==============================
Coordinates the overall optimization cycle, manages region agents,
and triggers guardrails and self-checks.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Dict, List, Any
import pandas as pd

from agents.region_agent import RegionAgent
from agents.guardrail_agent import GuardrailAgent
from agents.negotiation_protocol import NegotiationProtocol
from self_check import SelfChecker
from audit_module import AuditModule


class OrchestratorAgent:
    """Global coordinator for the multi-agent system."""

    def __init__(self, config: dict):
        self.config = config
        self.regions = config.get("capacity", {}).keys()
        self.region_agents = {r: RegionAgent(r, config) for r in self.regions}
        self.guardrail = GuardrailAgent(config)
        self.negotiator = NegotiationProtocol(config)
        self.self_checker = SelfChecker(config)
        self.audit = AuditModule(config)

    def run_optimization_cycle(self, data: dict) -> dict:
        """
        Run the full optimization cycle (simulated synchronously for the MVP).
        """
        weekly_demand = data["weekly_demand"]
        current_inventory = data["current_inventory"]
        sku_summary = data["sku_summary"]
        sku_classes = dict(zip(sku_summary["Product_ID"], sku_summary["SKU_Class"]))
        capacity = data["capacity"]
        transfer_costs = data["transfer_costs"]
        lead_times = data["lead_times"]

        # 1. Forecasting & Placement (Parallelizable)
        all_forecasts = []
        all_placements = []
        for r_name, agent in self.region_agents.items():
            f = agent.forecast_demand(weekly_demand, sku_classes)
            if not f.empty:
                all_forecasts.append(f)
                p = agent.compute_placement(f, current_inventory, sku_summary, capacity)
                all_placements.append(p)

        if not all_placements:
            return {"status": "error", "message": "No placements generated"}

        full_placement = pd.concat(all_placements, ignore_index=True)

        # 2. Transfer Proposals
        all_proposals = []
        for r_name, agent in self.region_agents.items():
            t = agent.propose_transfers(full_placement, transfer_costs, lead_times, sku_summary)
            if not t.empty:
                all_proposals.extend(t.to_dict("records"))

        # 3. Guardrail Validation
        validation_result = self.guardrail.validate_all(all_proposals, capacity)
        validated_proposals = validation_result["validated_transfers"]

        # 4. Negotiation (Conflict Resolution)
        negotiation_result = self.negotiator.run_negotiation_round(validated_proposals)
        final_transfers = negotiation_result["resolved_proposals"]

        # 5. Audit Logging & Human-in-the-Loop categorization
        pending_approval = []
        auto_approved = []
        for t in final_transfers:
            self.audit.generate_audit_entry(t, t.get("SKU_Class", "C"))
            if t.get("Status") == "pending_approval":
                pending_approval.append(t)
            elif t.get("Status") == "auto_approved":
                auto_approved.append(t)

        # 6. Metrics & Self-Check
        plan_metrics = self._compute_plan_metrics(full_placement, final_transfers)
        self_check_res = self.self_checker.check_plan(plan_metrics, transfers=final_transfers, capacity=capacity)

        # 7. Cost Report
        agent_costs = [a.get_cost_report() for a in self.region_agents.values()]
        total_decision_cost = sum(c["total_cost_inr"] for c in agent_costs)

        return {
            "status": "success",
            "placement": full_placement,
            "transfers": final_transfers,
            "pending_approval": pending_approval,
            "auto_approved": auto_approved,
            "audit_logs": self.audit.get_all_logs(),
            "self_check": self_check_res,
            "metrics": plan_metrics,
            "agent_costs": agent_costs,
            "total_decision_cost": total_decision_cost,
        }

    def _compute_plan_metrics(self, placement: pd.DataFrame, transfers: List[dict]) -> dict:
        total_tc = sum(t.get("Total_Transfer_Cost", 0) for t in transfers if t.get("is_valid"))
        
        # Simplified metrics for the cycle
        total_shortage = placement[placement["Surplus_Deficit"] < 0]["Surplus_Deficit"].abs().sum()
        total_demand = placement["Avg_Weekly_Demand"].sum() * self.config.get("optimization", {}).get("planning_horizon_weeks", 12)
        
        sl = 1.0 - (total_shortage / total_demand) if total_demand > 0 else 1.0
        
        a_class = placement[placement["SKU_Class"] == "A"]
        a_short = a_class[a_class["Surplus_Deficit"] < 0]["Surplus_Deficit"].abs().sum()
        a_dem = a_class["Avg_Weekly_Demand"].sum() * 12
        a_sl = 1.0 - (a_short / a_dem) if a_dem > 0 else 1.0

        return {
            "total_transfer_cost": total_tc,
            "service_level": sl,
            "a_class_instock_rate": a_sl,
            "total_shortage": total_shortage,
        }
