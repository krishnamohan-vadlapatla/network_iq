import unittest
from src.self_check import SelfChecker

class TestSelfCheck(unittest.TestCase):
    def setUp(self):
        self.config = {
            "optimization": {
                "service_level_target": 0.95
            }
        }
        self.checker = SelfChecker(self.config)

    def test_check_plan_passed(self):
        metrics = {
            "service_level": 0.97,
            "capacity_violations": 0,
            "a_class_instock_rate": 0.99
        }
        res = self.checker.check_plan(metrics)
        self.assertEqual(res["overall_status"], "PASSED")
        self.assertEqual(res["passed_checks"], 2)

    def test_check_plan_failed(self):
        metrics = {
            "service_level": 0.90, # fails target of 0.95
            "capacity_violations": 0,
            "a_class_instock_rate": 0.99
        }
        res = self.checker.check_plan(metrics)
        self.assertEqual(res["overall_status"], "FAILED")
        self.assertEqual(res["failed_checks"], 1)

if __name__ == "__main__":
    unittest.main()
