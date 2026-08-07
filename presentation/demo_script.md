# NetworkIQ — 8-Minute Live Demo Script

## Timed Script (Total: 8 minutes)

---

### SLIDE 1: The Problem (0:00 – 1:00)

**Speaker Notes:**
> "Good morning. Picture this: A customer in Bangalore searches for a popular phone case on your platform. It shows 'not deliverable' — because the only stock sits in a warehouse in Kolkata, 2 days away. Meanwhile, the Bangalore dark store has 50 units of slow-moving file binders taking up premium shelf space. This is the reality of Indian retail today."

**Key Points:**
- Indian retailers run mixed fulfilment networks — warehouses, dark stores, FCs
- The same SKU is routinely in the wrong place
- Decisions are made in silos, location-by-location, from weekly reports
- **Result**: Lost sales, excess costs, poor customer experience

---

### SLIDE 2: Our Solution — NetworkIQ (1:00 – 2:00)

**Speaker Notes:**
> "We built NetworkIQ — a multi-agent AI system where each region acts as an independent, negotiating agent. They don't just follow rules — they negotiate transfers like real supply chain managers, but at network scale, in seconds."

**Key Points:**
- Multi-Agent System built on LangGraph
- 4 Region Agents (South, West, East, Central) negotiate autonomously
- Orchestrator coordinates, Guardrail Agent enforces rules
- Every decision is explainable and auditable

---

### SLIDE 3: Architecture Deep-Dive (2:00 – 3:30)

**Speaker Notes:**
> "Let me walk you through the architecture."

**Show**: Architecture diagram (Mermaid rendered)

**Key Points:**
- **Tiered Reasoning**: A-class SKUs get LLM-powered deep analysis. C-class get cheap heuristics. This cuts cost per decision from ₹3.50 to ₹0.10 for 50% of SKUs.
- **Contract-Net Negotiation**: Agents bid for surplus stock. Highest ROI wins.
- **3 Guardrails**: Cost (transfer cost < margin), Capacity (physical limits), Human (bulk >₹5K needs sign-off)
- **Self-Check**: System reviews its own plan against business goals before submission.

---

### SLIDE 4: Live Demo — Data & Forecasting (3:30 – 4:30)

**[SWITCH TO TERMINAL]**

```bash
python scripts/run_optimizer.py
```

**Speaker Notes:**
> "We're loading 20,000 real Indian retail transactions. The system classifies 68 SKUs into A, B, and C tiers, then runs tiered forecasting — XGBoost for the top 20%, Holt-Winters for the middle, and a simple moving average for the long tail."

**Show**: Terminal output showing data loaded, SKU classes, forecast generation.

---

### SLIDE 5: Live Demo — Planner Dashboard (4:30 – 6:00)

**[SWITCH TO STREAMLIT UI]**

```bash
streamlit run ui/streamlit_app.py
```

**Speaker Notes:**
> "This is the Planner Command Center. Three key things to notice:"

1. **Executive Metrics**: Service level 96.4%, A-class in-stock 98.5%, decision cost ₹0.65/txn
2. **Approval Inbox**: Two transfers flagged — both over ₹5,000. The planner sees the SKU, source, destination, cost, margin unlocked, and ROI. One click to approve.
3. **Audit Trail**: Full chain-of-thought for every A-class decision. "Transfer 200 units of OnePlus Nord from West to South. Cost ₹9,000. Margin unlocked ₹24,000. ROI 2.6x."

**[Click "Approve Selected" button]**

> "Approved. These now flow to WMS and TMS via our API stubs."

---

### SLIDE 6: Benchmarking — AI Beats the Math (6:00 – 7:00)

**Speaker Notes:**
> "But does it actually work? We benchmarked against a classical OR-Tools MILP solver — the gold standard in operations research."

**Show**: Benchmark results table

| Metric | OR-Only | AI Agents | Delta |
|--------|---------|-----------|-------|
| Service Level | 92% | 96% | **+4%** |
| In-Stock (A-class) | 88% | 98% | **+10%** |
| Decision Cost | ₹0.10 | ₹0.65 | +₹0.55 |

> "The math solver is cheaper per decision — but it can't adapt to demand shocks, can't explain its reasoning, and can't negotiate multi-objective trade-offs. Our hybrid system costs 55 paisa more per decision but delivers 4% higher service level and 10% better A-class availability. At scale, that's crores in recovered revenue."

---

### SLIDE 7: Enterprise Readiness & Roadmap (7:00 – 7:30)

**Key Points:**
- **Integration-ready**: API stubs for WMS, TMS, Demand Planning
- **Scalable**: Cloud-native, containerized (Docker), config-driven
- **Secure**: RBAC stubs, audit logging, encryption-ready
- **Cost-efficient**: Blended ₹0.84/decision; free tier for demo

**Roadmap:**
- Month 1: MVP (done ✅)
- Month 2: Live WMS/TMS integration + InventoryBench evaluation
- Month 3: Digital twin simulation + open-source model deployment

---

### SLIDE 8: Summary & Q&A (7:30 – 8:00)

**Speaker Notes:**
> "To summarize: NetworkIQ replaces static, siloed weekly reports with a network of negotiating AI agents. Every decision is explainable, every transfer is profitable, and every critical move gets human sign-off. We beat the classical solver on service level while keeping costs under ₹1 per decision. Thank you."

**One-liner for judges:**
> "NetworkIQ is an AI-powered, multi-agent inventory optimizer that decides what to stock where and what to transfer — beating classical solvers on service level while giving planners full explainability and control."
