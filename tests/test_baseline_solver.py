import unittest
from src.baseline_solver import BaselineSolver

class TestBaselineSolver(unittest.TestCase):
    def setUp(self):
        self.config = {
            "optimization": {
                "holding_cost_rate": 0.02,
                "lost_sale_penalty_multiplier": 2.5,
                "planning_horizon_weeks": 1
            }
        }
        self.solver = BaselineSolver(self.config)

    def test_solve_feasible(self):
        demand = {"South": 100, "West": 50}
        inventory = {"South": 150, "West": 10}
        capacity = {"South": {"total_units": 200}, "West": {"total_units": 200}}
        transfer_costs = {("South", "West"): 5, ("West", "South"): 5}
        
        res = self.solver.solve(demand, inventory, capacity, transfer_costs, avg_price=100)
        self.assertEqual(res["status"], "optimal")
        self.assertTrue(len(res["transfers"]) > 0)
        # Should transfer from South to West to fulfill West's deficit
        transfer = res["transfers"][0]
        self.assertEqual(transfer["from"], "South")
        self.assertEqual(transfer["to"], "West")

if __name__ == "__main__":
    unittest.main()
