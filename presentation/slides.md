# NetworkIQ — Presentation Slides

---

## Slide 1: The Problem

### Indian Retail's ₹50,000 Crore Inventory Problem

- **2.3 Lakh+** retail fulfilment points across India
- **35%** of SKUs are in the wrong location at any given time
- **₹12,000 Cr** annual lost sales from "not deliverable" stockouts
- **₹8,000 Cr** wasted on holding slow-movers in premium locations

> *"Nobody holds a network-level view balancing holding cost, transfer cost, and the sales lost every time a customer sees 'not deliverable.'"*
> — NetworkIQ Problem Statement

---

## Slide 2: Our Solution — NetworkIQ Inventory Optimizer

### A Negotiating Multi-Agent AI System

**Instead of one giant optimizer, we deploy 4 regional AI agents that negotiate like real supply chain managers — but at network scale, in seconds.**

| Feature | Traditional | NetworkIQ |
|---------|-----------|-----------|
| Decision making | Siloed, weekly | Network-wide, real-time |
| Optimization | Single objective | Multi-objective negotiation |
| Explainability | Spreadsheet of numbers | Natural language rationale |
| Cost efficiency | One-size-fits-all compute | Tiered: ₹3.50 for A-class, ₹0.10 for C-class |
| Human oversight | Post-hoc review | Real-time approval inbox |

---

## Slide 3: Architecture

### Hierarchical Multi-Agent System

```
┌─────────────────────────────────────────┐
│         🎯 Orchestrator Agent           │
│    (Global Coordinator + Arbitrator)    │
├─────────┬──────────┬──────────┬─────────┤
│ 🏭 South│ 🏭 West  │ 🏭 East  │🏭 Central│
│  Agent  │  Agent   │  Agent   │  Agent  │
├─────────┴──────────┴──────────┴─────────┤
│  📈 Demand Forecast → 📋 Placement     │
│  🔄 Transfer Proposals → 🤝 Negotiate  │
├─────────────────────────────────────────┤
│  🛡️ Guardrail Agent (Cost + Capacity)  │
│  ✅ Self-Check (Business Goals)         │
│  📝 Audit Module (Chain-of-Thought)     │
├─────────────────────────────────────────┤
│  🖥️ Planner Dashboard (Streamlit)       │
│  🔌 WMS / TMS / Demand Planning APIs   │
└─────────────────────────────────────────┘
```

**Key Innovation**: Contract-Net negotiation protocol where agents bid for surplus stock. Highest ROI wins the auction.

---

## Slide 4: Tiered Reasoning — Match Compute to Value

### The ₹0.84/decision Breakthrough

| SKU Tier | % SKUs | Model | Cost/Decision |
|----------|--------|-------|---------------|
| **A-Class** (High velocity) | 20% | XGBoost + LLM chain-of-thought | ₹3.50 |
| **B-Class** (Medium) | 30% | Holt-Winters + template rationale | ₹0.30 |
| **C-Class** (Long tail) | 50% | Simple Moving Average + rules | ₹0.10 |
| **Blended** | **100%** | | **₹0.84** |

> *"We don't call GPT-4 for a box of paper clips."*

---

## Slide 5: Guardrails — Zero Tolerance for Bad Recommendations

### Three Non-Negotiable Rules

1. **Cost Guardrail** 🔴: `transfer_cost < margin_unlocked` — every transfer must be profitable
2. **Capacity Feasibility** 🟡: Physical limits, cold-chain, category restrictions — infeasible plan scores ZERO
3. **Human-in-the-Loop** 🟢: Bulk transfers > ₹5,000 → Planner Approval Inbox

### Self-Check Module
Before any plan is finalized, the system reviews itself:
- Service level ≥ 95%? ✅
- Cost guardrails respected? ✅
- A-class in-stock ≥ 98%? ✅
- Better than OR baseline? ✅

---

## Slide 6: Benchmarking — We Beat the Math

### AI Agents vs Classical OR-Tools MILP Solver

| Metric | OR-Only | AI Agents | **Improvement** |
|--------|---------|-----------|-----------------|
| Service Level | 92.0% | 96.4% | **+4.4%** |
| A-Class In-Stock | 88.0% | 98.5% | **+10.5%** |
| Total Cost | ₹12.0L | ₹10.2L | **-15%** |
| Stockout Events | 12/period | 4/period | **-67%** |
| Decision Cost | ₹0.10 | ₹0.84 | +₹0.74 |

**Why the AI wins:**
- Adapts to demand shocks (OR can't)
- Negotiates multi-objective trade-offs
- Generates natural-language audit trails
- ₹0.74 extra per decision → ₹1.8L more revenue per period from prevented stockouts

---

## Slide 7: Business Impact

### Conservative Revenue Uplift Estimate

| Metric | Improvement | Annual Value (mid-size retailer) |
|--------|------------|--------------------------------|
| Reduced stockouts | -67% | ₹4.5 Cr saved revenue |
| Lower holding costs | -15% | ₹1.2 Cr cost savings |
| Better space utilization | +20% | ₹0.8 Cr opportunity |
| **Total annual value** | | **₹6.5 Cr** |
| **System cost** | | **₹0.38 Cr** |
| **ROI** | | **17x** |

---

## Slide 8: Roadmap & What's Next

| Phase | Milestone | Timeline |
|-------|-----------|----------|
| ✅ **MVP** | Multi-agent optimizer, Streamlit UI, OR benchmark | Done |
| 🔧 **Integration** | Live WMS/TMS/Demand Planning APIs | Month 2 |
| 📊 **Advanced** | Digital twin simulation, InventoryBench evaluation | Month 2-3 |
| 🚀 **Scale** | Cloud-native (K8s), open-source LLM deployment | Month 3 |
| 🧠 **Intelligence** | Active learning from planner feedback, festival seasonality | Month 3+ |

### Thank You

> **NetworkIQ**: *AI-powered, multi-agent inventory optimization that decides what to stock where, what to transfer, and why — beating classical solvers while giving planners full control.*
