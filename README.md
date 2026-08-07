<div align="center">
  <h1>🚀 NetworkIQ Inventory Optimizer</h1>
  <p><b>AI-Driven Multi-Agent Inventory Optimization for Modern Indian Retail Networks</b></p>
  <p><i>A Top 1% Hackathon MVP built for the NetworkIQ Student Problem Statement</i></p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
  [![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0-purple.svg)](https://langchain.com)
  [![OR-Tools](https://img.shields.io/badge/OR--Tools-9.8-orange.svg)](https://developers.google.com/optimization)
  [![Streamlit](https://img.shields.io/badge/Streamlit-UI-red.svg)](https://streamlit.io)
</div>

<br>

## NetworkIQ

### The Problem
In the rapidly evolving Indian retail and q-commerce landscape, inventory optimization across a mixed fulfillment network—spanning central warehouses, city fulfillment centers (FCs), and hyper-local dark stores—is a mission-critical challenge. Traditional systems rely on siloed, static weekly reports. This disjointed approach leads to fast-moving essentials getting stuck in distant warehouses, while premium quick-commerce shelf space is choked by slow-moving stock, resulting in chronic stockouts and bloated holding costs.

### What NetworkIQ Does
NetworkIQ is a decentralized, **Multi-Agent System (MAS)** that replaces static reporting with dynamic, real-time negotiation. It utilizes specialized AI agents representing distinct physical fulfillment nodes to balance demand shocks, physical capacities, cold-chain requirements, and transfer costs autonomously. It guarantees **Zero-Loss Transfers** via strict mathematical guardrails, ensuring that no stock movement ever costs more than the margin it unlocks.

### Current MVP
The current MVP provides a robust simulation environment where multi-agent negotiations take place over a dataset of Indian Store Data. It includes a Google OR-Tools benchmark to prove ROI, an intelligent LangGraph orchestration engine, and a fully functional Human-in-the-Loop Streamlit dashboard for planner approval of high-stakes stock transfers.

---

## Guiding Principles
1. **Never Violate the Math:** LLMs cannot be trusted with raw arithmetic. All profitability and capacity calculations are strictly enforced by deterministic Python algorithms before the LLM can finalize a decision.
2. **Compute matches Value:** Never spend ₹2 on an API call to save ₹1. Inference costs are aggressively optimized.
3. **Transparency over Black Boxes:** A planner must be able to read and understand exactly *why* the AI recommended a massive transfer. Explainability is a hard requirement.

---

## Success Metrics
- **Increased In-Stock Rate:** Targeting a 99%+ availability for A-Class SKUs at high-velocity Q-commerce nodes.
- **Lower Total Network Cost:** Minimizing the sum of holding costs, transfer costs, and lost-sales penalties compared to classical EOQ (Economic Order Quantity) baselines.
- **Cost-Per-Decision Optimization:** Keeping the blended average cost of an AI recommendation strictly under ₹0.10.

---

## Product Flow
1. **Data Ingestion:** The system pulls live stock levels and demand forecasts.
2. **Deficit/Surplus Identification:** Regional agents independently identify inventory imbalances.
3. **Agent Negotiation:** Agents communicate via the Orchestrator, proposing transfers and bidding on holding/transfer costs.
4. **Self-Check & Guardrails:** The Auditor Agent runs deterministic checks against capacity and financial margin.
5. **Human-in-the-Loop:** Bulk/expensive transfers are halted and pushed to the Streamlit UI.
6. **Execution:** Approved transfers are dispatched to the TMS/WMS APIs.

---

## How a Recommendation is Evaluated
Every single proposed transfer is rigorously evaluated through a three-stage funnel:
1. **Is there Demand?** A statistical model (Holt-Winters/XGBoost) must prove future demand exists at the destination.
2. **Is it Physically Possible?** The destination node must have the volumetric (CBM) and specialized (cold-chain) capacity.
3. **Is it Profitable?** `Transfer Cost < Margin Unlocked`. If the cost to ship the item is greater than the gross profit of selling it, the transfer is killed instantly.

---

## AI-Agent Design
The core architecture completely avoids the brittle "mega-prompt" paradigm, utilizing a distributed LangGraph state machine:
- **Regional Negotiator Agents:** Each real-world node operates as an independent agent handling its localized inventory state.
- **The Orchestrator:** Acts as the network's global broker, coordinating multi-node negotiations and finding the lowest-cost transfer paths.
- **The Guardrail & Auditor Agent:** Generates natural-language chain-of-thought justifications and enforces deterministic constraints.

---

## Tiered Reasoning and Cost Control
Supply chain networks contain millions of SKUs. We route SKU decisions dynamically based on their financial classification:
- **A-Class SKUs (High Value / High Velocity):** Routed to deep-reasoning LLMs (GPT-4o / Claude 3.5). The LLM processes unstructured demand shocks and complex multi-node negotiations.
- **B/C-Class SKUs (Long Tail / Low Value):** Routed to lightning-fast classical rules engines or local open-source models (Llama-3), ensuring the cost-per-decision remains virtually zero.

---

## Data We Will Use
The system is designed to ingest granular, India-specific retail data:
- **Indian Store Data:** Time-series CSV detailing historical SKU-level sales and profit margins in ₹.
- **Location Capacity Profiles:** Node volumetric capacity (CBM) and restrictions.
- **Transfer Cost Matrix:** Cost (₹) and lead time (days) to move stock between any two nodes.
- **Product Attributes:** SKU volume, perishability, and velocity classification.

---

## Technology Direction & Tech Stack
This project is built using enterprise-grade technologies to ensure massive scalability:
- **AI & Agent Orchestration:** `LangGraph`, `LangChain`
- **Large Language Models:** `GPT-4o`, `Claude 3.5`, `Llama-3`
- **Mathematical Optimization:** `Google OR-Tools` (GLOP solver)
- **Forecasting:** `Statsmodels`, `XGBoost`, `Pandas`
- **Frontend / UX:** `Streamlit`, `Plotly`

---

## Core Backend Services
- **Agent State Manager:** Maintains the LangGraph execution state, allowing asynchronous pauses for human approvals.
- **Optimization Engine:** The MILP (Mixed-Integer Linear Programming) solver handling base-stock placement.
- **Audit Logger:** A secure, append-only service that records every parameter, prompt, and LLM output for compliance.

---

## Production Architecture We Are Building
In a full production rollout, NetworkIQ shifts from a local script to a resilient, cloud-native architecture:
- **Compute:** Ray clusters (KubeRay) on Kubernetes for distributed, horizontal scaling of LangGraph agents.
- **Data Lakehouse:** Delta Lake / Databricks for unifying streaming WMS telemetry and batch demand forecasts.
- **Event Bus:** Apache Kafka for real-time trigger events (e.g., immediate re-routing upon a sudden stockout).

---

## API Plan
NetworkIQ is designed with an API-first approach, built to plug seamlessly into existing retail backbones. (Stubs provided in `src/integration`):
1. `GET /api/wms/inventory`: Polls real-time physical stock and bin capacity.
2. `GET /api/tms/routes`: Fetches live transfer costs and dynamic lead times between nodes.
3. `POST /api/wms/transfers`: Dispatches approved stock movement orders to the warehouse execution system.

---

## Engineering Decisions
To build a solution capable of passing rigorous evaluation by leading e-commerce companies, we made several critical architectural choices:
- **Multi-Agent Systems vs. Single LLM Prompting:** Giving one LLM the entire network state exceeds context windows and causes reasoning hallucinations. Isolated agents negotiating locally scale infinitely.
- **Hybrid AI + Classical MILP:** Pure math solvers (MILP) find the absolute minimum cost in static environments but fail spectacularly under non-stationary demand shocks. Our AI uses OR-Tools for the heavy lifting and overlays AI for negotiation and shock-adaptation.

---

## Roadmap
- **Phase 1 (MVP):** Multi-agent optimizer on static CSVs, Streamlit Human-in-the-Loop approval dashboard, OR-Tools benchmark. *(Completed)*
- **Phase 2 (Integration):** Live API connectors for WMS/TMS, implementation of Kafka event bus for real-time triggers.
- **Phase 3 (Scale):** Deployment to Kubernetes via Ray Serve, rolling out localized open-source LLMs to further drive down inference costs.

---

## Getting Started

### 1. Clone & Setup
```bash
git clone https://github.com/your-org/networkiq-inventory-optimizer.git
cd networkiq-inventory-optimizer

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate 

pip install -r requirements.txt
```

### 2. Run the Benchmark (AI vs Math)
Execute the benchmark simulation that injects demand shocks to prove the MAS outperforms the classical baseline.
```bash
python scripts/run_benchmark.py
```

### 3. Launch the Planner Dashboard (UI)
Start the Human-in-the-Loop interface.
```bash
streamlit run ui/streamlit_app.py
```
*(Open http://localhost:8501 in your browser)*

---

<div align="center">
  <p><b>Built for the Future of Indian Retail Fulfillment.</b></p>
</div>
