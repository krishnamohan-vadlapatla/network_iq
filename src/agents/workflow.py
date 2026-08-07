"""
NetworkIQ — LangGraph Workflow Definition
=========================================
Defines the StateGraph for the multi-agent system, linking the orchestrator,
region agents, guardrails, and human-in-the-loop nodes.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from agents.state import NetworkIQState
from agents.orchestrator_agent import OrchestratorAgent


def initialize_workflow(config: dict) -> StateGraph:
    """Build the LangGraph workflow."""
    
    orchestrator = OrchestratorAgent(config)

    # Node: Orchestrator runs the cycle
    def run_optimization(state: NetworkIQState) -> NetworkIQState:
        data = {
            "weekly_demand": state["weekly_demand"],
            "current_inventory": state.get("current_inventory"),
            "sku_summary": state["sku_data"],
            "capacity": state["capacity"],
            "transfer_costs": state["transfer_costs"],
            "lead_times": state["lead_times"],
        }
        
        result = orchestrator.run_optimization_cycle(data)
        
        state["placements"] = result.get("placement")
        state["resolved_transfers"] = result.get("transfers", [])
        state["pending_approvals"] = result.get("pending_approval", [])
        state["approved_transfers"] = result.get("auto_approved", [])
        state["audit_logs"] = result.get("audit_logs", [])
        state["self_check_results"] = result.get("self_check", {})
        state["plan_metrics"] = result.get("metrics", {})
        
        return state

    # Node: Human-in-the-Loop Wait State
    def human_approval_queue(state: NetworkIQState) -> NetworkIQState:
        # In a real deployed LangGraph, this would be a breakpoint or wait state.
        # For this MVP, we just collect the pending approvals for the UI to consume.
        state["current_phase"] = "awaiting_approval" if state["pending_approvals"] else "completed"
        return state

    # Build Graph
    workflow = StateGraph(NetworkIQState)
    
    workflow.add_node("optimize", run_optimization)
    workflow.add_node("human_approval", human_approval_queue)
    
    workflow.set_entry_point("optimize")
    workflow.add_edge("optimize", "human_approval")
    workflow.add_edge("human_approval", END)
    
    return workflow.compile()
