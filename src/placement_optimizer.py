"""
NetworkIQ — Placement Optimizer
================================
EOQ, safety stock, reorder point calculations.
Capacity-constrained allocation with A>B>C priority.
"""

import numpy as np
import pandas as pd
from typing import Dict, List


class PlacementOptimizer:
    """Optimizes SKU placement quantities at each location."""

    def __init__(self, config: dict):
        self.config = config
        opt = config.get("optimization", {})
        self.holding_rate = opt.get("holding_cost_rate", 0.02)
        self.z_score = opt.get("safety_stock_z_score", 1.65)
        self.service_target = opt.get("service_level_target", 0.95)

    def compute_eoq(self, annual_demand: float, ordering_cost: float = 500,
                    holding_cost_per_unit: float = 10) -> float:
        """Economic Order Quantity."""
        if annual_demand <= 0 or holding_cost_per_unit <= 0:
            return 0
        return np.sqrt(2 * annual_demand * ordering_cost / holding_cost_per_unit)

    def compute_safety_stock(self, demand_std: float, lead_time_days: float = 3) -> float:
        """Safety stock = z * σ_demand * √lead_time."""
        lead_time_weeks = lead_time_days / 7.0
        return self.z_score * demand_std * np.sqrt(lead_time_weeks)

    def compute_reorder_point(self, avg_weekly_demand: float, lead_time_days: float,
                              safety_stock: float) -> float:
        """ROP = average demand during lead time + safety stock."""
        lead_time_weeks = lead_time_days / 7.0
        return avg_weekly_demand * lead_time_weeks + safety_stock

    def optimize_placement(self, forecasts: pd.DataFrame,
                           current_inventory: pd.DataFrame,
                           sku_summary: pd.DataFrame,
                           capacity: Dict[str, dict],
                           regions: List[str]) -> pd.DataFrame:
        """
        Compute optimal placement for all SKU-region combinations.
        Returns DataFrame with target stock levels, surplus/deficit, and priority.
        """
        # Aggregate forecasts to get avg weekly demand and std per SKU-region
        agg = (forecasts.groupby(["Product_ID", "Region"])
               .agg(Avg_Forecast=("Forecast", "mean"),
                    Std_Forecast=("Forecast", "std"))
               .reset_index())
        agg["Std_Forecast"] = agg["Std_Forecast"].fillna(0)

        # Merge with SKU info
        sku_info = sku_summary[["Product_ID", "SKU_Class", "Unit_Volume",
                                "Avg_Price"]].drop_duplicates("Product_ID")
        if "Avg_Price" not in sku_info.columns:
            sku_info["Avg_Price"] = 500
        agg = agg.merge(sku_info, on="Product_ID", how="left")
        agg["SKU_Class"] = agg["SKU_Class"].fillna("C")
        agg["Avg_Price"] = agg["Avg_Price"].fillna(500)
        agg["Unit_Volume"] = agg["Unit_Volume"].fillna(1.0)

        # Compute targets
        results = []
        for _, row in agg.iterrows():
            hc = self.holding_rate * row["Avg_Price"]
            annual_d = row["Avg_Forecast"] * 52
            eoq = self.compute_eoq(annual_d, holding_cost_per_unit=max(hc, 0.1))
            ss = self.compute_safety_stock(row["Std_Forecast"])
            rop = self.compute_reorder_point(row["Avg_Forecast"], 3, ss)
            target = round(rop + eoq / 2)  # Avg cycle stock + safety stock

            # Priority: A=3, B=2, C=1
            priority = {"A": 3, "B": 2, "C": 1}.get(row["SKU_Class"], 1)

            results.append({
                "Product_ID": row["Product_ID"],
                "Region": row["Region"],
                "SKU_Class": row["SKU_Class"],
                "Avg_Weekly_Demand": round(row["Avg_Forecast"], 2),
                "Demand_Std": round(row["Std_Forecast"], 2),
                "EOQ": round(eoq, 1),
                "Safety_Stock": round(ss, 1),
                "Reorder_Point": round(rop, 1),
                "Target_Stock": target,
                "Unit_Volume": row["Unit_Volume"],
                "Priority": priority,
            })

        placement_df = pd.DataFrame(results)

        # Merge current inventory
        if len(current_inventory) > 0:
            placement_df = placement_df.merge(
                current_inventory[["Product_ID", "Region", "Current_Stock"]],
                on=["Product_ID", "Region"], how="left"
            )
            placement_df["Current_Stock"] = placement_df["Current_Stock"].fillna(0)
        else:
            placement_df["Current_Stock"] = 0

        placement_df["Surplus_Deficit"] = placement_df["Current_Stock"] - placement_df["Target_Stock"]
        placement_df["Status"] = placement_df["Surplus_Deficit"].apply(
            lambda x: "surplus" if x > 0 else ("deficit" if x < 0 else "balanced")
        )

        # Enforce capacity constraints per region
        for region in regions:
            mask = placement_df["Region"] == region
            region_df = placement_df.loc[mask].copy()
            cap = capacity.get(region, {}).get("total_units", 99999)
            total_volume = (region_df["Target_Stock"] * region_df["Unit_Volume"]).sum()

            if total_volume > cap:
                # Scale down by priority — C-class first
                scale_factor = cap / total_volume
                for cls in ["C", "B", "A"]:
                    cls_mask = mask & (placement_df["SKU_Class"] == cls)
                    placement_df.loc[cls_mask, "Target_Stock"] = (
                        placement_df.loc[cls_mask, "Target_Stock"] * scale_factor
                    ).round().astype(int)
                placement_df.loc[mask, "Capacity_Constrained"] = True
            else:
                placement_df.loc[mask, "Capacity_Constrained"] = False

        placement_df["Surplus_Deficit"] = placement_df["Current_Stock"] - placement_df["Target_Stock"]
        return placement_df
