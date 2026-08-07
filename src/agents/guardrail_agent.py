"""
NetworkIQ — Guardrail Agent
==============================
Validates every transfer against cost, capacity, and business constraints.
Acts as the system's self-checker before human review.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Dict, List, Tuple


class GuardrailAgent:
    """Enforces cost guardrails, capacity limits, and approval thresholds."""

    def __init__(self, config: dict):
        self.config = config
        self.approval_threshold = config.get("transfers", {}).get("approval_threshold_inr", 5000)
        self.cost_guardrail = config.get("transfers", {}).get("cost_guardrail", True)

    def validate_transfer(self, transfer: dict, capacity: Dict[str, dict],
                          current_usage: Dict[str, float] = None) -> dict:
        """
        Validate a single transfer against all guardrails.
        Returns the transfer dict with validation results added.
        """
        result = transfer.copy()
        checks = []
        is_valid = True

        # 1. Cost guardrail: transfer_cost < margin_unlocked
        tc = transfer.get("Total_Transfer_Cost", 0)
        mu = transfer.get("Margin_Unlocked", 0)
        if self.cost_guardrail and tc >= mu:
            checks.append({
                "rule": "cost_guardrail",
                "passed": False,
                "detail": f"Transfer cost ₹{tc:,.0f} >= margin unlocked ₹{mu:,.0f}"
            })
            is_valid = False
        else:
            checks.append({
                "rule": "cost_guardrail",
                "passed": True,
                "detail": f"Transfer cost ₹{tc:,.0f} < margin unlocked ₹{mu:,.0f} (ROI: {mu/tc:.1f}x)" if tc > 0 else "Zero cost"
            })

        # 2. Capacity feasibility at destination
        to_region = transfer.get("To_Region", "")
        qty = transfer.get("Quantity", 0)
        vol = transfer.get("Unit_Volume", 1.0)
        cap = capacity.get(to_region, {}).get("total_units", 99999)
        usage = (current_usage or {}).get(to_region, 0)
        if usage + qty * vol > cap:
            checks.append({
                "rule": "capacity_feasibility",
                "passed": False,
                "detail": f"Destination {to_region} would exceed capacity: {usage + qty * vol:.0f} > {cap}"
            })
            is_valid = False
        else:
            checks.append({
                "rule": "capacity_feasibility",
                "passed": True,
                "detail": f"Destination {to_region} has capacity: {usage + qty * vol:.0f} / {cap}"
            })

        # 3. Non-negative quantity
        if qty <= 0:
            checks.append({
                "rule": "positive_quantity",
                "passed": False,
                "detail": "Transfer quantity must be positive"
            })
            is_valid = False

        # 4. Human-in-the-loop threshold
        requires_approval = tc > self.approval_threshold
        checks.append({
            "rule": "approval_threshold",
            "requires_human": requires_approval,
            "detail": f"Transfer cost ₹{tc:,.0f} {'exceeds' if requires_approval else 'within'} threshold ₹{self.approval_threshold:,}"
        })

        result["guardrail_checks"] = checks
        result["is_valid"] = is_valid
        result["Requires_Approval"] = requires_approval
        if not is_valid:
            result["Status"] = "rejected_guardrail"
            result["Rejection_Reason"] = "; ".join(
                c["detail"] for c in checks if not c.get("passed", True)
            )
        elif requires_approval:
            result["Status"] = "pending_approval"
        else:
            result["Status"] = "auto_approved"

        return result

    def validate_all(self, transfers: List[dict], capacity: Dict[str, dict],
                     current_usage: Dict[str, float] = None) -> dict:
        """Validate all transfers and return summary."""
        validated = []
        for t in transfers:
            validated.append(self.validate_transfer(t, capacity, current_usage))

        approved = [t for t in validated if t["Status"] == "auto_approved"]
        pending = [t for t in validated if t["Status"] == "pending_approval"]
        rejected = [t for t in validated if t["Status"] == "rejected_guardrail"]

        return {
            "validated_transfers": validated,
            "summary": {
                "total": len(validated),
                "auto_approved": len(approved),
                "pending_approval": len(pending),
                "rejected": len(rejected),
                "total_approved_cost": sum(t.get("Total_Transfer_Cost", 0) for t in approved),
                "total_pending_cost": sum(t.get("Total_Transfer_Cost", 0) for t in pending),
            }
        }
