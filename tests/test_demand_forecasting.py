import unittest
import pandas as pd
from src.demand_forecasting import DemandForecaster

class TestDemandForecasting(unittest.TestCase):
    def setUp(self):
        # Setup config
        self.config = {
            "optimization": {"planning_horizon_weeks": 4},
            "random_seed": 42,
            "reasoning": {
                "a_class_cost": 3.50,
                "b_class_cost": 0.30,
                "c_class_cost": 0.10
            }
        }
        self.forecaster = DemandForecaster(self.config)
        # Create small time series
        self.mock_demand = pd.DataFrame({
            "Product_ID": ["FUR-CH-1"] * 10,
            "Region": ["South"] * 10,
            "Year": [2019] * 10,
            "Week": list(range(1, 11)),
            "Year_Week": [f"2019_W{w:02d}" for w in range(1, 11)],
            "Weekly_Demand": [10, 12, 11, 13, 15, 14, 16, 15, 17, 18],
            "Weekly_Sales": [1000] * 10,
            "Weekly_Profit": [100] * 10,
            "Avg_Discount": [0.0] * 10
        })

    def test_forecast_sma(self):
        # SMA should work with small datasets
        sku_classes = {"FUR-CH-1": "C"}
        forecasts = self.forecaster.forecast_all(self.mock_demand, sku_classes, ["South"])
        self.assertEqual(len(forecasts), 4) # Horizon is 4 weeks
        self.assertEqual(forecasts["Model_Used"].iloc[0], "sma")

    def test_forecast_holtwinters(self):
        sku_classes = {"FUR-CH-1": "B"}
        forecasts = self.forecaster.forecast_all(self.mock_demand, sku_classes, ["South"])
        self.assertEqual(len(forecasts), 4)

if __name__ == "__main__":
    unittest.main()
