import unittest
import pandas as pd
from src.data_loader import prepare_full_dataset
from src.agents.orchestrator_agent import OrchestratorAgent

class TestIntegration(unittest.TestCase):
    def test_end_to_end_flow(self):
        # Load the generated synthetic dataset
        data = prepare_full_dataset()
        orchestrator = OrchestratorAgent(data["config"])
        
        # Run optimization cycle
        result = orchestrator.run_optimization_cycle(data)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("transfers", result)
        self.assertIn("metrics", result)
        self.assertIn("self_check", result)
        self.assertIn("total_decision_cost", result)

if __name__ == "__main__":
    unittest.main()
