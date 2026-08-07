"""
NetworkIQ — Negotiation Protocol
================================
Implements the contract-net protocol for multi-agent negotiation.
Resolves conflicts when multiple regions bid for the same surplus/deficit.
"""

from typing import List, Dict


class NegotiationProtocol:
    """Manages the negotiation rounds between region agents."""

    def __init__(self, config: dict):
        self.config = config
        self.max_rounds = config.get("optimization", {}).get("max_negotiation_rounds", 3)

    def resolve_conflicts(self, proposals: List[dict]) -> List[dict]:
        """
        Resolve conflicts where multiple agents propose transfers for the same
        SKU that exceed the available surplus or deficit.
        """
        # Group by (Product_ID, From_Region) to check source capacity
        source_groups = {}
        for p in proposals:
            if not p.get("is_valid", True):
                continue
            key = (p["Product_ID"], p["From_Region"])
            if key not in source_groups:
                source_groups[key] = []
            source_groups[key].append(p)

        resolved_proposals = []
        
        # We need a way to know the actual max available at the source.
        # In a real distributed system, agents would broadcast their available surplus.
        # For this MVP, we assume the first proposal's "max_from_source" or similar 
        # is implicitly available, but we'll arbitrate purely by ROI.
        
        for key, group in source_groups.items():
            if len(group) == 1:
                resolved_proposals.append(group[0])
                continue

            # Sort by ROI descending
            sorted_group = sorted(group, key=lambda x: x.get("ROI", 0), reverse=True)
            
            # For simplicity in this MVP, we just take the highest ROI proposal 
            # and reject the others if they compete for the same source.
            # A more advanced implementation would partially fulfill based on available stock.
            best = sorted_group[0]
            resolved_proposals.append(best)
            
            for other in sorted_group[1:]:
                other_copy = dict(other)
                other_copy["Status"] = "rejected_negotiation"
                other_copy["Rejection_Reason"] = f"Lost auction to higher ROI transfer to {best['To_Region']}"
                other_copy["is_valid"] = False
                resolved_proposals.append(other_copy)

        return resolved_proposals

    def run_negotiation_round(self, all_proposals: List[dict]) -> dict:
        """
        Run a single round of negotiation.
        """
        resolved = self.resolve_conflicts(all_proposals)
        
        accepted = [p for p in resolved if p.get("Status") not in ("rejected_negotiation", "rejected_guardrail")]
        rejected = [p for p in resolved if p.get("Status") in ("rejected_negotiation", "rejected_guardrail")]
        
        return {
            "resolved_proposals": resolved,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
        }
