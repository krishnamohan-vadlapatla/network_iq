"""
NetworkIQ — Data Loader & Preprocessor
=======================================
Ingests the Indian Store Data CSV, cleans it, computes derived features
(ABC classification, velocity, capacity profiles), and synthesizes
missing fields (transfer costs, lead times, current inventory).

All synthesis is seeded for reproducibility.
"""

import os
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional


def load_config(config_path: str = None) -> dict:
    """Load the central YAML configuration."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_raw_data(csv_path: str = None) -> pd.DataFrame:
    """Load the Indian Store Data CSV."""
    if csv_path is None:
        csv_path = Path(__file__).parent.parent / "data" / "indian_store_data.csv"
    
    df = pd.read_csv(csv_path, encoding="utf-8")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize the raw dataset."""
    # Standardize column names
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("-", "_")
    
    # Ensure required columns exist (Superstore-style)
    required = ["Order_Date", "Region", "Category", "Sub_Category",
                 "Product_ID", "Product_Name", "Sales", "Quantity", "Profit"]
    
    # Handle common column name variations
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_").replace("-", "_")
        if "order" in col_lower and "date" in col_lower:
            rename_map[col] = "Order_Date"
        elif col_lower == "sub_category" or col_lower == "subcategory":
            rename_map[col] = "Sub_Category"
        elif col_lower == "product_id":
            rename_map[col] = "Product_ID"
        elif col_lower == "product_name":
            rename_map[col] = "Product_Name"
    
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Parse dates
    if "Order_Date" in df.columns:
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["Order_Date"])
    
    # Drop rows with missing critical values
    critical = [c for c in ["Sales", "Quantity", "Profit", "Region", "Category"] if c in df.columns]
    df = df.dropna(subset=critical)
    
    # Ensure numeric types
    for col in ["Sales", "Quantity", "Discount", "Profit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.dropna(subset=["Sales", "Quantity"])
    
    return df.reset_index(drop=True)


def compute_abc_classification(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Classify SKUs into A/B/C tiers based on cumulative revenue share.
    A-class: top 20% of SKUs by total revenue.
    B-class: next 30%.
    C-class: bottom 50%.
    """
    a_thresh = config["sku_tiers"]["a_class_threshold"]
    b_thresh = config["sku_tiers"]["b_class_threshold"]
    
    # Aggregate revenue by product
    sku_revenue = (
        df.groupby("Product_ID")["Sales"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    sku_revenue.columns = ["Product_ID", "Total_Revenue"]
    
    # Cumulative share
    total = sku_revenue["Total_Revenue"].sum()
    sku_revenue["Cumulative_Share"] = sku_revenue["Total_Revenue"].cumsum() / total
    
    # Classify
    def classify(share):
        if share <= a_thresh:
            return "A"
        elif share <= b_thresh:
            return "B"
        return "C"
    
    sku_revenue["SKU_Class"] = sku_revenue["Cumulative_Share"].apply(classify)
    
    # Merge back
    df = df.merge(sku_revenue[["Product_ID", "SKU_Class", "Total_Revenue"]], on="Product_ID", how="left")
    
    return df


def compute_product_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive product attributes: unit volume, perishability flag.
    Based on Sub_Category since the dataset doesn't have these natively.
    """
    # Volume mapping (cubic units — proxy for shelf space)
    volume_map = {
        "Phones": 0.5, "Accessories": 0.3, "Paper": 0.2,
        "Binders": 0.4, "Storage": 1.5, "Art": 0.3,
        "Envelopes": 0.2, "Labels": 0.1, "Fasteners": 0.1,
        "Appliances": 2.0, "Furnishings": 2.5, "Bookcases": 3.0,
        "Chairs": 3.0, "Tables": 3.5, "Copiers": 2.0,
        "Machines": 2.5, "Supplies": 0.5,
    }
    
    if "Sub_Category" in df.columns:
        df["Unit_Volume"] = df["Sub_Category"].map(volume_map).fillna(1.0)
    else:
        df["Unit_Volume"] = 1.0
    
    # Perishability — none in Superstore data, all non-perishable
    df["Is_Perishable"] = False
    
    return df


def compute_weekly_demand(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate demand to SKU × Region × Week level for forecasting.
    """
    if "Order_Date" not in df.columns:
        raise ValueError("Order_Date column required for demand computation")
    
    df["Week"] = df["Order_Date"].dt.isocalendar().week.astype(int)
    df["Year"] = df["Order_Date"].dt.year
    df["Year_Week"] = df["Year"].astype(str) + "_W" + df["Week"].astype(str).str.zfill(2)
    
    weekly = (
        df.groupby(["Product_ID", "Region", "Year", "Week", "Year_Week"])
        .agg(
            Weekly_Demand=("Quantity", "sum"),
            Weekly_Sales=("Sales", "sum"),
            Weekly_Profit=("Profit", "sum"),
            Avg_Discount=("Discount", "mean"),
        )
        .reset_index()
    )
    
    return weekly


def compute_current_inventory(df: pd.DataFrame, config: dict, seed: int = 42) -> pd.DataFrame:
    """
    Synthesize current inventory positions from historical sales data.
    current_stock ≈ avg_weekly_sales × 6 (6-week cover), with noise.
    """
    rng = np.random.RandomState(seed)
    
    # Average weekly demand by product × region
    weekly = compute_weekly_demand(df)
    avg_demand = (
        weekly.groupby(["Product_ID", "Region"])["Weekly_Demand"]
        .mean()
        .reset_index()
    )
    avg_demand.columns = ["Product_ID", "Region", "Avg_Weekly_Demand"]
    
    # Synthesize stock = avg_demand × (4 to 8 weeks cover)
    avg_demand["Current_Stock"] = (
        avg_demand["Avg_Weekly_Demand"] * rng.uniform(4, 8, size=len(avg_demand))
    ).round().astype(int).clip(lower=0)
    
    return avg_demand


def get_transfer_cost_matrix(config: dict) -> Dict[Tuple[str, str], float]:
    """Build symmetric transfer cost matrix from config."""
    costs = {}
    for route, cost in config["transfer_costs"].items():
        parts = route.split("-")
        if len(parts) == 2:
            costs[(parts[0], parts[1])] = cost
            costs[(parts[1], parts[0])] = cost
    return costs


def get_lead_time_matrix(config: dict) -> Dict[Tuple[str, str], int]:
    """Build symmetric lead time matrix from config."""
    times = {}
    for route, lt in config["lead_times"].items():
        parts = route.split("-")
        if len(parts) == 2:
            times[(parts[0], parts[1])] = lt
            times[(parts[1], parts[0])] = lt
    return times


def get_capacity_profiles(config: dict) -> Dict[str, dict]:
    """Get per-region capacity profiles."""
    return config["capacity"]


def prepare_full_dataset(csv_path: str = None, config_path: str = None) -> dict:
    """
    Master function: load, clean, enrich, and return all data needed
    by the optimization system.
    
    Returns a dictionary with:
        - raw_df: cleaned DataFrame
        - weekly_demand: weekly demand aggregation
        - current_inventory: synthesized current positions
        - transfer_costs: cost matrix dict
        - lead_times: lead time matrix dict
        - capacity: capacity profiles dict
        - config: full configuration dict
        - sku_summary: SKU-level summary with ABC class
    """
    config = load_config(config_path)
    seed = config.get("random_seed", 42)
    
    # Load and clean
    df = load_raw_data(csv_path)
    df = clean_data(df)
    
    # Enrich
    df = compute_abc_classification(df, config)
    df = compute_product_attributes(df)
    
    # Aggregations
    weekly_demand = compute_weekly_demand(df)
    current_inventory = compute_current_inventory(df, config, seed)
    
    # SKU summary
    sku_summary = (
        df.groupby(["Product_ID", "Category", "Sub_Category", "SKU_Class", "Unit_Volume", "Is_Perishable"])
        .agg(
            Total_Sales=("Sales", "sum"),
            Total_Quantity=("Quantity", "sum"),
            Total_Profit=("Profit", "sum"),
            Avg_Price=("Sales", "mean"),
        )
        .reset_index()
    )
    
    # Matrices
    transfer_costs = get_transfer_cost_matrix(config)
    lead_times = get_lead_time_matrix(config)
    capacity = get_capacity_profiles(config)
    
    return {
        "raw_df": df,
        "weekly_demand": weekly_demand,
        "current_inventory": current_inventory,
        "transfer_costs": transfer_costs,
        "lead_times": lead_times,
        "capacity": capacity,
        "config": config,
        "sku_summary": sku_summary,
        "regions": sorted(df["Region"].unique().tolist()),
    }


if __name__ == "__main__":
    data = prepare_full_dataset()
    print(f"Loaded {len(data['raw_df']):,} rows")
    print(f"Regions: {data['regions']}")
    print(f"SKU Classes: {data['raw_df']['SKU_Class'].value_counts().to_dict()}")
    print(f"Weekly demand records: {len(data['weekly_demand']):,}")
    print(f"Current inventory records: {len(data['current_inventory']):,}")
