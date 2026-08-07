"""
NetworkIQ — Region Agent (Negotiator)
=======================================
Each region is an independent agent that:
  1. Forecasts local demand (tiered by SKU class)
  2. Computes optimal placement
  3. Proposes transfers (surplus/deficit)
  4. Negotiates with peer agents
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from typing import Dict, List, Any

from demand_forecasting import DemandForecaster
from placement_optimizer import PlacementOptimizer
from transfer_optimizer import TransferOptimizer
from audit_module import AuditModule


class RegionAgent:
    """
    Autonomous agent for a single region.
    Handles forecasting, placement, transfer proposals, and negotiation.
    """

    def __init__(self, region: str, config: dict):
        self.region = region
        self.config = config
        self.forecaster = DemandForecaster(config)
        self.placement_opt = PlacementOptimizer(config)
        self.transfer_opt = TransferOptimizer(config)
        self.audit = AuditModule(config)
        self.proposals: List[dict] = []
        self.cost_tracker = {"A": 0, "B": 0, "C": 0, "count_A": 0, "count_B": 0, "count_C": 0}

    def forecast_demand(self, weekly_demand: pd.DataFrame,
                        sku_classes: Dict[str, str]) -> pd.DataFrame:
        """Generate demand forecasts for this region's SKUs."""
        region_demand = weekly_demand[weekly_demand["Region"] == self.region].copy()
        if len(region_demand) == 0:
            return pd.DataFrame()

        forecasts = self.forecaster.forecast_all(
            region_demand, sku_classes, [self.region]
        )

        # Track cost per tier
        for cls in ["A", "B", "C"]:
            cls_count = len(forecasts[forecasts["SKU_Class"] == cls])
            self.cost_tracker[f"count_{cls}"] += cls_count

        return forecasts

    def compute_placement(self, forecasts: pd.DataFrame,
                          current_inventory: pd.DataFrame,
                          sku_summary: pd.DataFrame,
                          capacity: Dict[str, dict]) -> pd.DataFrame:
        """Compute optimal placement for this region."""
        region_forecasts = forecasts[forecasts["Region"] == self.region].copy()
        region_inventory = current_inventory[
            current_inventory["Region"] == self.region
        ].copy()

        placement = self.placement_opt.optimize_placement(
            region_forecasts, region_inventory, sku_summary,
            capacity, [self.region]
        )
        return placement

    def propose_transfers(self, placement: pd.DataFrame,
                          transfer_costs: Dict, lead_times: Dict,
                          sku_summary: pd.DataFrame) -> pd.DataFrame:
        """Generate transfer proposals based on surplus/deficit."""
        transfers = self.transfer_opt.generate_transfers(
            placement, transfer_costs, lead_times, sku_summary
        )
        self.proposals = transfers.to_dict("records") if len(transfers) > 0 else []
        return transfers

    def evaluate_peer_proposal(self, proposal: dict) -> dict:
        """
        Evaluate a transfer proposal from another region.
        Returns acceptance/rejection with reasoning.
        """
        # Check if this region is the source
        if proposal.get("From_Region") != self.region:
            return {"accepted": True, "reason": "Not source region"}

        qty = proposal.get("Quantity", 0)
        tc = proposal.get("Total_Transfer_Cost", 0)
        margin = proposal.get("Margin_Unlocked", 0)

        # Would this transfer leave us understocked?
        if proposal.get("Passes_Cost_Guardrail", False) and margin > tc:
            return {
                "accepted": True,
                "reason": f"Transfer of {qty} units is profitable (ROI: {margin/tc:.1f}x)"
            }
        else:
            return {
                "accepted": False,
                "reason": f"Transfer cost ₹{tc:.0f} exceeds margin ₹{margin:.0f}"
            }

    def get_cost_report(self) -> dict:
        """Report cost-per-decision for this region's agent."""
        reasoning = self.config.get("reasoning", {})
        total = 0
        for cls in ["A", "B", "C"]:
            count = self.cost_tracker.get(f"count_{cls}", 0)
            cost = reasoning.get(f"{cls.lower()}_class_cost", 0.10)
            total += count * cost
        return {
            "region": self.region,
            "total_decisions": sum(self.cost_tracker.get(f"count_{c}", 0) for c in "ABC"),
            "total_cost_inr": round(total, 2),
            "breakdown": {
                cls: {
                    "count": self.cost_tracker.get(f"count_{cls}", 0),
                    "cost_per": reasoning.get(f"{cls.lower()}_class_cost", 0.10),
                } for cls in ["A", "B", "C"]
            }
        }
