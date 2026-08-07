# NetworkIQ — AI Workflow Documentation

## End-to-End Optimization Pipeline

### Step 1: Data Ingestion & Preprocessing
- **Input**: Indian Store Data CSV (20K+ rows, 2019–2023)
- **Process**: 
  - Column normalization and date parsing
  - ABC classification (A: top 20% revenue, B: next 30%, C: bottom 50%)
  - Product attribute derivation (unit volume, perishability)
  - Synthetic generation of transfer costs, lead times, and capacity profiles
- **Output**: Enriched DataFrame + SKU summary with velocity classes

### Step 2: Tiered Demand Forecasting
| SKU Class | Model | Cost/Decision | Rationale |
|-----------|-------|---------------|-----------|
| A (top 20%) | XGBoost with feature engineering | ₹3.50 | High accuracy needed for high-value SKUs |
| B (next 30%) | Holt-Winters Exponential Smoothing | ₹0.30 | Good accuracy at moderate compute |
| C (bottom 50%) | Simple Moving Average (4-week) | ₹0.10 | Minimal compute for long-tail SKUs |

**Features engineered for A-class**: lag values, rolling mean/std, week-of-year seasonality, trend component, discount effects.

### Step 3: Placement Optimization
- **EOQ** (Economic Order Quantity) per SKU-region
- **Safety stock** = z × σ_demand × √lead_time (z=1.65 for 95% service level)
- **Reorder point** = avg demand during lead time + safety stock
- **Target stock** = ROP + EOQ/2 (average cycle stock)
- **Capacity-constrained allocation**: Priority A > B > C; C-class scaled down first when capacity is tight

### Step 4: Transfer Proposal Generation
- Identify surplus/deficit per SKU-region from (current_stock − target_stock)
- Generate transfers with full cost-benefit analysis:
  - Transfer cost (₹/unit × quantity)
  - Margin unlocked (₹/unit margin × quantity)
  - ROI = margin_unlocked / transfer_cost
  - Lead time impact
- **Cost guardrail**: Reject transfers where transfer_cost ≥ margin_unlocked
- **Approval flag**: Transfers with cost > ₹5,000 require planner sign-off

### Step 5: Multi-Agent Negotiation
- **Protocol**: Contract-Net with auction-based conflict resolution
- **Conflict**: When multiple regions bid for the same surplus SKU, highest ROI wins
- **Max rounds**: 3 (configurable)
- **Orchestrator** coordinates and arbitrates

### Step 6: Guardrail Validation
Every transfer is validated against:
1. ✅ Cost guardrail: `transfer_cost < margin_unlocked`
2. ✅ Capacity feasibility: destination has room
3. ✅ Positive quantity check
4. ⚠️ Approval threshold: cost > ₹5,000 → pending human approval

### Step 7: Self-Check
Automated validation against business goals:
- Service level ≥ 95%?
- All cost guardrails respected?
- No capacity violations?
- Improvement over baseline?
- A-class in-stock rate ≥ 98%?

### Step 8: Human-in-the-Loop Approval
- Bulk transfers flagged in Streamlit "Approval Inbox"
- Each item shows: SKU, from/to, quantity, cost, margin, ROI, and chain-of-thought rationale
- Planner can: Approve, Reject, or Request More Info
- All actions logged to audit trail

### Step 9: Execution & Feedback
- Approved plans can be forwarded via WMS/TMS API stubs
- Actuals fed back for model retraining (feedback loop)

## Tiered Reasoning Cost Model

| Component | A-Class | B-Class | C-Class |
|-----------|---------|---------|---------|
| Forecasting | XGBoost (₹3.50) | Holt-Winters (₹0.30) | SMA (₹0.10) |
| Placement | Full EOQ+SS | Standard EOQ | Simple threshold |
| Transfer reasoning | LLM chain-of-thought | Template-based | Rule-based |
| Audit | LLM natural language | Template fill | Auto-generated |
| **Blended cost** | **₹3.50/decision** | **₹0.30/decision** | **₹0.10/decision** |
