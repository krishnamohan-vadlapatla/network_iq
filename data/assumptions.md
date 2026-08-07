# Data Synthesis Assumptions — NetworkIQ Inventory Optimizer

## Overview

The Indian Store Data (Kaggle Superstore-style dataset) provides sales, profit, and product
information but lacks several fields required for a full inventory optimization system.
This document details every synthesized data element and the rationale behind it.

## Synthesized Elements

### 1. Transfer Cost Matrix (₹ per unit)

Based on average Indian logistics costs for inter-city freight (2024 rates):

| Route | Cost (₹/unit) | Basis |
|-------|---------------|-------|
| South ↔ West | 45 | Mumbai-Chennai corridor, ~1,300 km |
| South ↔ East | 65 | Chennai-Kolkata, ~1,700 km |
| South ↔ Central | 55 | Chennai-Nagpur, ~1,200 km |
| West ↔ East | 70 | Mumbai-Kolkata, ~2,000 km |
| West ↔ Central | 40 | Mumbai-Nagpur, ~800 km |
| East ↔ Central | 50 | Kolkata-Nagpur, ~1,100 km |

**Source**: Industry average of ₹3–5 per unit-km for standard retail goods.

### 2. Lead Time Matrix (days)

| Route | Days | Basis |
|-------|------|-------|
| South ↔ West | 3 | Road + rail mix |
| South ↔ East | 4 | Longer route, fewer direct connections |
| South ↔ Central | 3 | Central hub connectivity |
| West ↔ East | 4 | Cross-country |
| West ↔ Central | 2 | Short corridor |
| East ↔ Central | 3 | Moderate distance |

### 3. Location Capacity (units)

| Region | Total Capacity | Cold-Chain Capacity | Basis |
|--------|---------------|--------------------:|-------|
| South | 15,000 | 2,000 | Mid-sized regional hub |
| West | 18,000 | 2,500 | Largest market (Mumbai) |
| East | 12,000 | 1,500 | Smaller market |
| Central | 14,000 | 1,800 | Secondary hub |

### 4. Current Inventory Positions

Derived from the last 4 weeks of sales data:
- `current_stock = avg_weekly_sales × 6` (6-week cover assumption)
- Capped at regional capacity

### 5. Product Attributes

| Attribute | Derivation |
|-----------|-----------|
| **Velocity Class (A/B/C)** | ABC analysis on cumulative revenue share: A = top 20%, B = next 30%, C = bottom 50% |
| **Perishability** | Category-based: "Office Supplies" → non-perishable; all others → non-perishable (no food in dataset) |
| **Unit Volume** | Sub-Category based: Phones/Accessories → small (0.5); Chairs/Tables → large (3.0); others → medium (1.0) |
| **Margin** | Directly from `Profit` column in the dataset |

### 6. Demand Forecasting Inputs

- Historical demand = `Quantity` aggregated by SKU × Region × Week
- Seasonality derived from `Order Date` patterns
- Discount effect from `Discount` column

## Reproducibility

All synthetic data generation uses `random_seed: 42` from `config.yaml`.
Functions are deterministic given the same input CSV and seed.
