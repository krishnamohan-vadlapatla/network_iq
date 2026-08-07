"""
NetworkIQ — Multi-Agent Shared State
======================================
TypedDict state schema for the LangGraph workflow.
All agents read/write to this shared state.
"""

from typing import TypedDict, List, Dict, Optional, Any


class NetworkIQState(TypedDict):
    """Shared state for the multi-agent optimization workflow."""
    # Input data
    regions: List[str]
    sku_data: Dict[str, Any]           # enriched SKU data
    weekly_demand: Any                  # DataFrame (serialized)
    sku_classes: Dict[str, str]        # Product_ID -> A/B/C
    transfer_costs: Dict[str, float]
    lead_times: Dict[str, int]
    capacity: Dict[str, Dict]
    config: Dict[str, Any]

    # Agent outputs
    forecasts: Dict[str, Any]          # region -> forecast results
    placements: Dict[str, Any]         # region -> placement proposals
    proposals: Dict[str, List]         # region -> transfer proposals
    
    # Negotiation
    negotiation_round: int
    negotiation_history: List[Dict]
    resolved_transfers: List[Dict]
    
    # Guardrail & audit
    guardrail_results: Dict[str, Any]
    audit_logs: List[Dict]
    
    # Self-check
    self_check_results: Dict[str, Any]
    
    # Human-in-the-loop
    pending_approvals: List[Dict]
    approved_transfers: List[Dict]
    rejected_transfers: List[Dict]
    
    # Metrics
    plan_metrics: Dict[str, float]
    baseline_metrics: Dict[str, float]
    
    # Control
    current_phase: str
    errors: List[str]
