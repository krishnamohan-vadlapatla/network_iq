import unittest
import pandas as pd
from src.agents.region_agent import RegionAgent
from src.agents.guardrail_agent import GuardrailAgent
from src.agents.negotiation_protocol import NegotiationProtocol

class TestAgents(unittest.TestCase):
    def setUp(self):
        self.config = {
            "optimization": {
                "holding_cost_rate": 0.02,
                "lost_sale_penalty_multiplier": 2.5,
                "planning_horizon_weeks": 4,
                "max_negotiation_rounds": 3
            },
            "transfers": {
                "approval_threshold_inr": 5000,
                "cost_guardrail": True,
                "max_transfer_pct_of_stock": 0.40
            },
            "reasoning": {
                "a_class_cost": 3.50,
                "b_class_cost": 0.30,
                "c_class_cost": 0.10
            }
        }
        self.region_agent = RegionAgent("South", self.config)
        self.guardrail = GuardrailAgent(self.config)
        self.negotiator = NegotiationProtocol(self.config)

    def test_guardrail_violation(self):
        # Transfer cost exceeds margin
        transfer = {
            "Product_ID": "FUR-CH-1",
            "From_Region": "South",
            "To_Region": "West",
            "Quantity": 100,
            "Total_Transfer_Cost": 5000,
            "Margin_Unlocked": 2000,
            "Passes_Cost_Guardrail": False,
            "Requires_Approval": False
        }
        capacity = {"West": {"total_units": 100}}
        res = self.guardrail.validate_transfer(transfer, capacity)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["Status"], "rejected_guardrail")

    def test_negotiation_protocol(self):
        proposals = [
            {
                "Product_ID": "FUR-CH-1",
                "From_Region": "South",
                "To_Region": "West",
                "ROI": 2.5,
                "is_valid": True
            },
            {
                "Product_ID": "FUR-CH-1",
                "From_Region": "South",
                "To_Region": "East",
                "ROI": 1.2,
                "is_valid": True
            }
        ]
        res = self.negotiator.resolve_conflicts(proposals)
        # Higher ROI (2.5) should be accepted, lower ROI (1.2) rejected due to conflict on same source
        accepted = [p for p in res if p.get("is_valid")]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["To_Region"], "West")

if __name__ == "__main__":
    unittest.main()
