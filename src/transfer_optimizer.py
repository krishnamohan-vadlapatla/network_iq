"""
NetworkIQ — Transfer Optimizer
================================
Generates transfer recommendations with cost-benefit analysis,
cost guardrail enforcement, and capacity feasibility checks.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


class TransferOptimizer:
    """Recommends inter-location transfers to rebalance inventory."""

    def __init__(self, config: dict):
        self.config = config
        self.approval_threshold = config.get("transfers", {}).get("approval_threshold_inr", 5000)
        self.max_transfer_pct = config.get("transfers", {}).get("max_transfer_pct_of_stock", 0.40)
        self.cost_guardrail = config.get("transfers", {}).get("cost_guardrail", True)

    def generate_transfers(self, placement: pd.DataFrame,
                           transfer_costs: Dict[Tuple[str, str], float],
                           lead_times: Dict[Tuple[str, str], int],
                           sku_summary: pd.DataFrame) -> pd.DataFrame:
        """
        Identify surplus/deficit SKUs and generate transfer proposals.
        Each transfer includes ROI, cost guardrail check, and approval flag.
        """
        # Separate surplus and deficit regions per SKU
        surplus = placement[placement["Surplus_Deficit"] > 0].copy()
        deficit = placement[placement["Surplus_Deficit"] < 0].copy()

        # Build profit margin lookup
        margin_lookup = {}
        if "Total_Profit" in sku_summary.columns and "Total_Quantity" in sku_summary.columns:
            for _, row in sku_summary.iterrows():
                qty = row.get("Total_Quantity", 1)
                if qty > 0:
                    margin_lookup[row["Product_ID"]] = row["Total_Profit"] / qty
        
        transfers = []
        for _, def_row in deficit.iterrows():
            pid = def_row["Product_ID"]
            def_region = def_row["Region"]
            need = abs(def_row["Surplus_Deficit"])
            sku_class = def_row.get("SKU_Class", "C")
            margin_per_unit = margin_lookup.get(pid, 50)  # default ₹50

            matching_surplus = surplus[
                (surplus["Product_ID"] == pid) & (surplus["Region"] != def_region)
            ].copy()

            for _, sur_row in matching_surplus.iterrows():
                sur_region = sur_row["Region"]
                available = sur_row["Surplus_Deficit"]
                max_from_source = sur_row["Current_Stock"] * self.max_transfer_pct

                qty = min(need, available, max_from_source)
                if qty < 1:
                    continue

                tc_per_unit = transfer_costs.get((sur_region, def_region), 100)
                total_tc = tc_per_unit * qty
                margin_unlocked = margin_per_unit * qty
                lt = lead_times.get((sur_region, def_region), 3)

                # Cost guardrail check
                passes_guardrail = total_tc < margin_unlocked if self.cost_guardrail else True
                roi = (margin_unlocked / total_tc) if total_tc > 0 else float("inf")

                # Human approval check
                requires_approval = total_tc > self.approval_threshold

                transfers.append({
                    "Product_ID": pid,
                    "SKU_Class": sku_class,
                    "From_Region": sur_region,
                    "To_Region": def_region,
                    "Quantity": round(qty),
                    "Transfer_Cost_Per_Unit": tc_per_unit,
                    "Total_Transfer_Cost": round(total_tc, 2),
                    "Margin_Per_Unit": round(margin_per_unit, 2),
                    "Margin_Unlocked": round(margin_unlocked, 2),
                    "ROI": round(roi, 2),
                    "Lead_Time_Days": lt,
                    "Passes_Cost_Guardrail": passes_guardrail,
                    "Requires_Approval": requires_approval,
                    "Status": "pending" if passes_guardrail else "rejected_guardrail",
                    "Rejection_Reason": "" if passes_guardrail else
                        f"Transfer cost ₹{total_tc:.0f} >= margin ₹{margin_unlocked:.0f}",
                })

                need -= qty
                if need < 1:
                    break

        transfer_df = pd.DataFrame(transfers)
        if len(transfer_df) > 0:
            transfer_df = transfer_df.sort_values("ROI", ascending=False).reset_index(drop=True)
        return transfer_df

    def get_transfer_summary(self, transfers: pd.DataFrame) -> dict:
        """Summary statistics for the transfer plan."""
        if len(transfers) == 0:
            return {"total_transfers": 0, "total_cost": 0, "total_margin": 0}
        feasible = transfers[transfers["Passes_Cost_Guardrail"]]
        return {
            "total_transfers": len(transfers),
            "feasible_transfers": len(feasible),
            "rejected_transfers": len(transfers) - len(feasible),
            "total_transfer_cost": round(feasible["Total_Transfer_Cost"].sum(), 2),
            "total_margin_unlocked": round(feasible["Margin_Unlocked"].sum(), 2),
            "avg_roi": round(feasible["ROI"].mean(), 2) if len(feasible) > 0 else 0,
            "transfers_needing_approval": int(feasible["Requires_Approval"].sum()),
            "by_sku_class": feasible["SKU_Class"].value_counts().to_dict(),
        }
