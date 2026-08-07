import unittest
import pandas as pd
from src.data_loader import clean_data, compute_abc_classification, compute_product_attributes

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        # Create a simple mock dataframe mimicking Indian Store Data
        self.mock_data = pd.DataFrame({
            "Row ID": [1, 2, 3],
            "Order ID": ["IN-2019-1", "IN-2019-2", "IN-2019-3"],
            "Order Date": ["01-01-2019", "02-01-2019", "03-01-2019"],
            "Region": ["South", "West", "East"],
            "Category": ["Furniture", "Office Supplies", "Technology"],
            "Sub-Category": ["Chairs", "Paper", "Phones"],
            "Product ID": ["FUR-CH-1", "OFF-PA-1", "TEC-PH-1"],
            "Product Name": ["Chair 1", "Paper 1", "Phone 1"],
            "Sales": [1000.0, 50.0, 5000.0],
            "Quantity": [2, 5, 1],
            "Discount": [0.0, 0.1, 0.2],
            "Profit": [100.0, 10.0, 500.0]
        })

    def test_clean_data(self):
        cleaned = clean_data(self.mock_data)
        self.assertIn("Order_Date", cleaned.columns)
        self.assertIn("Sub_Category", cleaned.columns)
        self.assertEqual(len(cleaned), 3)

    def test_abc_classification(self):
        cleaned = clean_data(self.mock_data)
        config = {
            "sku_tiers": {
                "a_class_threshold": 0.20,
                "b_class_threshold": 0.50
            }
        }
        abc = compute_abc_classification(cleaned, config)
        self.assertIn("SKU_Class", abc.columns)
        # Check that class is assigned (A, B, or C)
        self.assertTrue(all(c in ["A", "B", "C"] for c in abc["SKU_Class"]))

    def test_product_attributes(self):
        cleaned = clean_data(self.mock_data)
        attrs = compute_product_attributes(cleaned)
        self.assertIn("Unit_Volume", attrs.columns)
        self.assertIn("Is_Perishable", attrs.columns)
        self.assertEqual(attrs.loc[attrs["Sub_Category"] == "Phones", "Unit_Volume"].values[0], 0.5)

if __name__ == "__main__":
    unittest.main()
