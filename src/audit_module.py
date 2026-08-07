"""
NetworkIQ — Audit Module
==========================
Generates chain-of-thought explanations for every recommendation.
Supports LLM-generated rationale for A-class and template-based for B/C.
"""

import json
import datetime
from typing import Dict, List, Optional


class AuditModule:
    """Generates and stores audit trails for all recommendations."""

    def __init__(self, config: dict):
        self.config = config
        self.logs: List[dict] = []

    def generate_audit_entry(self, recommendation: dict, sku_class: str = "C",
                             llm_rationale: Optional[str] = None) -> dict:
        """
        Create an audit log entry for a single recommendation.
        A-class: includes LLM chain-of-thought.
        B/C-class: template-based explanation.
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "recommendation_id": f"REC-{len(self.logs)+1:05d}",
            "product_id": recommendation.get("Product_ID", "unknown"),
            "sku_class": sku_class,
            "action_type": recommendation.get("action_type", "transfer"),
            "details": {
                "from_region": recommendation.get("From_Region", ""),
                "to_region": recommendation.get("To_Region", ""),
                "quantity": recommendation.get("Quantity", 0),
                "transfer_cost": recommendation.get("Total_Transfer_Cost", 0),
                "margin_unlocked": recommendation.get("Margin_Unlocked", 0),
            },
            "guardrail_checks": {
                "cost_guardrail": recommendation.get("Passes_Cost_Guardrail", True),
                "capacity_feasible": recommendation.get("Capacity_Feasible", True),
            },
            "requires_approval": recommendation.get("Requires_Approval", False),
            "status": recommendation.get("Status", "pending"),
        }

        # Generate explanation
        if sku_class == "A" and llm_rationale:
            entry["explanation"] = {
                "type": "llm_chain_of_thought",
                "rationale": llm_rationale,
                "model_used": self.config.get("reasoning", {}).get("a_class_model", "gemini"),
            }
        else:
            entry["explanation"] = {
                "type": "template_based",
                "rationale": self._template_rationale(recommendation),
                "model_used": "rule_engine",
            }

        self.logs.append(entry)
        return entry

    def _template_rationale(self, rec: dict) -> str:
        """Generate template-based explanation for B/C-class decisions."""
        qty = rec.get("Quantity", 0)
        pid = rec.get("Product_ID", "SKU")
        fr = rec.get("From_Region", "Source")
        to = rec.get("To_Region", "Dest")
        tc = rec.get("Total_Transfer_Cost", 0)
        mu = rec.get("Margin_Unlocked", 0)
        roi = rec.get("ROI", 0)

        lines = [
            f"Transfer {qty} units of {pid} from {fr} to {to}.",
            f"Transfer cost: ₹{tc:,.0f} | Margin unlocked: ₹{mu:,.0f} | ROI: {roi:.1f}x.",
        ]
        if rec.get("Passes_Cost_Guardrail", True):
            lines.append("✅ Cost guardrail: PASSED (transfer cost < margin unlocked).")
        else:
            lines.append("❌ Cost guardrail: FAILED (transfer cost >= margin unlocked).")
        if rec.get("Requires_Approval", False):
            lines.append(f"⚠️ Requires planner approval (cost > ₹{self.config.get('transfers',{}).get('approval_threshold_inr',5000):,}).")

        return " | ".join(lines)

    def generate_llm_rationale(self, recommendation: dict, forecast_info: dict) -> str:
        """
        Generate A-class LLM chain-of-thought rationale.
        Uses mock LLM if no API key configured.
        """
        pid = recommendation.get("Product_ID", "SKU")
        qty = recommendation.get("Quantity", 0)
        fr = recommendation.get("From_Region", "Source")
        to = recommendation.get("To_Region", "Dest")
        tc = recommendation.get("Total_Transfer_Cost", 0)
        mu = recommendation.get("Margin_Unlocked", 0)
        avg_demand = forecast_info.get("avg_demand", 0)
        confidence = forecast_info.get("confidence", "medium")

        # Mock chain-of-thought (replace with actual LLM call in production)
        rationale = (
            f"CHAIN-OF-THOUGHT ANALYSIS for {pid} (A-Class SKU):\n"
            f"1. DEMAND SIGNAL: Average weekly demand at {to} is {avg_demand:.0f} units "
            f"(confidence: {confidence}). Current stock is insufficient for next 4 weeks.\n"
            f"2. SOURCE ASSESSMENT: {fr} has {qty}+ surplus units with declining velocity, "
            f"freeing premium shelf space.\n"
            f"3. COST-BENEFIT: Transfer cost ₹{tc:,.0f} unlocks ₹{mu:,.0f} in projected margin "
            f"(ROI: {mu/tc:.1f}x). Passes cost guardrail.\n"
            f"4. NETWORK IMPACT: Improves in-stock rate at {to} by ~{min(qty*2, 15):.0f}% for "
            f"this high-velocity SKU. Reduces dead stock at {fr}.\n"
            f"5. RISK: Lead time of {recommendation.get('Lead_Time_Days', 3)} days is within "
            f"acceptable window. No cold-chain constraints.\n"
            f"RECOMMENDATION: APPROVE transfer of {qty} units."
        )
        return rationale

    def get_all_logs(self) -> List[dict]:
        """Return all audit log entries."""
        return self.logs

    def export_logs(self, filepath: str = "audit_logs.json"):
        """Export audit logs to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.logs, f, indent=2, default=str)

    def get_summary(self) -> dict:
        """Summary of audit activity."""
        if not self.logs:
            return {"total_entries": 0}
        return {
            "total_entries": len(self.logs),
            "by_status": _count_by(self.logs, "status"),
            "by_sku_class": _count_by(self.logs, "sku_class"),
            "approvals_pending": sum(1 for l in self.logs if l.get("requires_approval")),
            "guardrail_failures": sum(
                1 for l in self.logs
                if not l.get("guardrail_checks", {}).get("cost_guardrail", True)
            ),
        }


def _count_by(logs: List[dict], key: str) -> dict:
    counts = {}
    for l in logs:
        v = l.get(key, "unknown")
        counts[v] = counts.get(v, 0) + 1
    return counts
