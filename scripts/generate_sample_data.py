"""
Generate Sample Indian Store Data
==================================
Creates a realistic, high-quality sample dataset mimicking the Kaggle Indian Store Data.
Includes: Order_Date, Region, Category, Sub_Category, Product_ID, Product_Name, Sales, Quantity, Discount, Profit.
"""

import pandas as pd
import numpy as np
import datetime
from pathlib import Path

def generate_data(num_rows=20000, seed=42):
    rng = np.random.RandomState(seed)
    
    regions = ["South", "West", "East", "Central"]
    categories = ["Furniture", "Office Supplies", "Technology"]
    
    subcategories = {
        "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
        "Office Supplies": ["Paper", "Binders", "Storage", "Art", "Envelopes", "Labels", "Fasteners", "Supplies", "Appliances"],
        "Technology": ["Phones", "Accessories", "Copiers", "Machines"]
    }
    
    product_names = {
        "Chairs": ["Godrej Ergonomic Chair", "Featherlite Mesh Chair", "Nilkamal Plastic Chair", "Supreme Plastic Chair"],
        "Tables": ["Godrej Executive Table", "Nilkamal Study Table", "Supreme Computer Table", "DeckUp Engineered Wood Table"],
        "Bookcases": ["Godrej Steel Almirah", "Nilkamal Book Shelf", "Supreme Storage Rack", "Bluewud Book Case"],
        "Furnishings": ["Bombay Dyeing Bed Sheet", "D'Decor Curtains", "Welspun Towel", "Raymond Cushions"],
        "Paper": ["Century Star A4 Paper", "JK Copier A4 Paper", "BILT Copy Power Paper", "TNPL Copier Paper"],
        "Binders": ["Solo Ring Binder", "Kangaroo File Binder", "Deluxe Lever Arch File", "Oddy Ring Binder"],
        "Storage": ["Godrej Plastic Drawer", "Nilkamal Plastic Cabinet", "Supreme Storage Box", "Solo Desktop Organizer"],
        "Art": ["Cello Colour Bombs", "Faber-Castell Crayons", "Camel Acrylic Paint", "Pidilite Fevicol"],
        "Envelopes": ["Solo Document Envelope", "Kangaroo Paper Envelope", "Oddy Window Envelope", "Deluxe Courier Envelope"],
        "Labels": ["Oddy Self Adhesive Labels", "Solo Label Sheets", "Deluxe Barcode Labels", "Kangaroo Sticker Labels"],
        "Fasteners": ["Kangaroo Stapler Pins", "Oddy Paper Clips", "Deluxe Binder Clips", "Solo Rubber Bands"],
        "Supplies": ["Solo Scissors", "Kangaroo Paper Punch", "Oddy Cutter", "Deluxe Ruler"],
        "Appliances": ["Bajaj Electric Kettle", "Usha Dry Iron", "Havells Induction Cooktop", "Philips Hair Dryer"],
        "Phones": ["OnePlus Nord", "Redmi Note 12", "Samsung Galaxy M34", "Realme Narzo"],
        "Accessories": ["SanDisk 64GB Pendrive", "Logitech Wireless Mouse", "Zebronics Keyboard", "Mi Power Bank 10000mAh"],
        "Copiers": ["Canon Pixma Printer", "HP Laserjet Printer", "Epson EcoTank Printer", "Brother Monochrome Printer"],
        "Machines": ["Lamination Machine", "Paper Shredding Machine", "Spiral Binding Machine", "Barcode Scanner"]
    }
    
    # Base prices in ₹
    base_prices = {
        "Chairs": 4500, "Tables": 7500, "Bookcases": 9000, "Furnishings": 1200,
        "Paper": 250, "Binders": 150, "Storage": 800, "Art": 100,
        "Envelopes": 80, "Labels": 50, "Fasteners": 40, "Supplies": 120,
        "Appliances": 2200, "Phones": 15000, "Accessories": 800, "Copiers": 12000,
        "Machines": 8500
    }

    start_date = datetime.date(2019, 1, 1)
    end_date = datetime.date(2023, 12, 31)
    time_delta = end_date - start_date
    
    data = []
    
    # Generate unique Product IDs
    sku_pool = {}
    for cat, sub_cats in subcategories.items():
        for sub in sub_cats:
            names = product_names[sub]
            sku_pool[sub] = []
            for i, name in enumerate(names):
                pid = f"{cat[:3]}-{sub[:2]}-1000{i+1}"
                sku_pool[sub].append((pid, name))

    print("Generating rows...")
    for row_id in range(1, num_rows + 1):
        # Pick random order date
        random_days = rng.randint(0, time_delta.days)
        order_date = start_date + datetime.timedelta(days=random_days)
        
        region = rng.choice(regions)
        category = rng.choice(categories)
        subcategory = rng.choice(subcategories[category])
        
        # Select SKU and product name
        skus = sku_pool[subcategory]
        pid, pname = skus[rng.randint(0, len(skus))]
        
        qty = int(rng.choice([1, 2, 3, 4, 5, 10], p=[0.4, 0.3, 0.15, 0.08, 0.05, 0.02]))
        base_p = base_prices[subcategory]
        # Add slight variation to price
        unit_price = base_p * rng.uniform(0.9, 1.1)
        
        discount = float(rng.choice([0.0, 0.1, 0.2, 0.3, 0.5], p=[0.7, 0.15, 0.08, 0.05, 0.02]))
        sales = round(unit_price * qty * (1 - discount), 2)
        
        # Profit margins: Furniture ~5-15%, Office Supplies ~15-35%, Tech ~10-25%
        margin_pct = rng.uniform(0.05, 0.15) if category == "Furniture" else \
                     rng.uniform(0.15, 0.35) if category == "Office Supplies" else \
                     rng.uniform(0.10, 0.25)
                     
        # Discount reduces profit directly
        profit = round((sales * margin_pct) - (unit_price * qty * discount * 0.5), 2)
        
        data.append({
            "Row ID": row_id,
            "Order ID": f"IN-{order_date.year}-{row_id + 100000}",
            "Order Date": order_date.strftime("%d-%m-%Y"),
            "Region": region,
            "Category": category,
            "Sub-Category": subcategory,
            "Product ID": pid,
            "Product Name": pname,
            "Sales": sales,
            "Quantity": qty,
            "Discount": discount,
            "Profit": profit
        })
        
    df = pd.DataFrame(data)
    
    # Save to data directory
    output_path = Path(__file__).parent.parent / "data" / "indian_store_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {num_rows} rows and saved to {output_path}")

if __name__ == "__main__":
    generate_data()
