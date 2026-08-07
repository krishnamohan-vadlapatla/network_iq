"""
NetworkIQ — Benchmarking Metrics
================================
Functions to compute KPIs for evaluating different optimization strategies.
"""

def compute_service_level(total_demand: float, total_shortage: float) -> float:
    """Percentage of demand fulfilled."""
    if total_demand <= 0:
        return 1.0
    return max(0.0, 1.0 - (total_shortage / total_demand))


def compute_holding_cost(total_inventory: float, holding_rate: float, 
                         avg_price: float, horizon: int) -> float:
    """Holding cost over the horizon."""
    return total_inventory * holding_rate * avg_price * horizon


def compute_penalty_cost(total_shortage: float, penalty_mult: float, 
                         avg_price: float) -> float:
    """Cost of lost sales."""
    return total_shortage * penalty_mult * avg_price


def compute_normalized_reward(total_cost: float, ideal_cost: float) -> float:
    """Normalized reward (1.0 = ideal cost, lower is worse)."""
    if total_cost <= 0:
        return 1.0
    return ideal_cost / total_cost


def compute_in_stock_rate(placement_df) -> float:
    """In-stock rate (fraction of locations with stock >= safety stock)."""
    if len(placement_df) == 0:
        return 1.0
    in_stock = placement_df[placement_df["Surplus_Deficit"] >= 0]
    return len(in_stock) / len(placement_df)
