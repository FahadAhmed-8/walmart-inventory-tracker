# backend/data_prep.py
import pandas as pd
import json
import datetime
import os
import random

# Path to your downloaded Kaggle dataset: "Retail Store Inventory Forecasting Dataset"
# This file should be in the same directory as this script.
DATASET_PATH = 'retail_inventory_forecast.csv'

def prepare_firestore_data(csv_path):
    """
    Reads the retail inventory CSV, processes it, and generates
    NDJSON files suitable for MongoDB (and Firestore) import.
    Generates 'inventory.json', 'products.json', and 'stores.json' locally.
    Adds a random 'min_replenish_time', a derived 'base_safety_stock',
    and a 'supplier_category_reliability' to products.
    """
    if not os.path.exists(csv_path):
        print(f"Error: Dataset not found at '{csv_path}'.")
        print("Please ensure 'retail_inventory_forecast.csv' is in the same directory as this script.")
        return

    try:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip() # Clean column names

        required_cols = ['Store ID', 'Product ID', 'Inventory Level', 'Units Sold', 'Category', 'Price', 'Region']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: Missing one or more required columns in '{csv_path}'.")
            print(f"Expected columns: {required_cols}")
            return

        print("Starting data preparation for database import...")

        # Calculate average units sold per product across the entire dataset
        # This will be used to derive a more realistic base_safety_stock
        avg_units_sold_per_product = df.groupby('Product ID')['Units Sold'].mean().fillna(0)

        # --- Prepare Products Data ---
        products_data = {}
        # Iterate through unique product IDs to ensure each product gets a single, consistent entry
        for product_id_str in df['Product ID'].unique():
            product_id = str(product_id_str)
            
            # Find a representative row for this product to get category, price
            # This assumes product attributes like category and price are consistent for a given product ID
            product_row = df[df['Product ID'] == product_id_str].iloc[0]

            # Get the average units sold for this product
            avg_sales = avg_units_sold_per_product.get(product_id_str, 0)
            
            # Calculate base_safety_stock: 15-25% of average sales, with a minimum of 10
            # Adding a small random factor to introduce some variability
            calculated_base_safety_stock = max(10, round(avg_sales * random.uniform(0.15, 0.25)))

            products_data[product_id] = {
                'product_id': product_id,
                'category': product_row['Category'],
                'price': float(product_row['Price']),
                'name': f"Product {product_id}", # Mock name
                'min_replenish_time': random.randint(3, 20), # Random replenishment time (3-20 days)
                'base_safety_stock': calculated_base_safety_stock, # NEW: Derived base safety stock
                'supplier_category_reliability': round(random.uniform(0.7, 0.99), 2) # NEW: Random reliability (0.7 to 0.99)
            }
        products_list = list(products_data.values())
        print(f"Prepared {len(products_list)} unique products.")

        # --- Prepare Stores Data ---
        stores_data = {}
        for _, row in df.iterrows():
            store_id = str(row['Store ID'])
            if store_id not in stores_data:
                stores_data[store_id] = {
                    'store_id': store_id,
                    'region': row['Region'],
                    'name': f"Store {store_id}" # Mock name
                }
        stores_list = list(stores_data.values())
        print(f"Prepared {len(stores_list)} unique stores.")

        # --- Prepare Inventory Data ---
        inventory_items = {}
        for _, row in df.iterrows():
            store_id = str(row['Store ID'])
            product_id = str(row['Product ID'])
            doc_key = f"{store_id}_{product_id}" # Using a key to ensure uniqueness per store-product pair

            # This will keep the last entry if duplicates exist for same store-product in the CSV
            inventory_items[doc_key] = { 
                'store_id': store_id,
                'product_id': product_id,
                'current_stock': int(row['Inventory Level']),
                'last_updated': datetime.datetime.now().isoformat(), # ISO format for datetime
                'daily_sales_simulation_base': max(1, int(row['Units Sold'])) # Ensure min 1 to avoid division by zero
            }
        inventory_list = list(inventory_items.values())
        print(f"Prepared {len(inventory_list)} unique inventory items.")

        def write_ndjson(data_list, filename):
            with open(filename, 'w') as f:
                for item in data_list:
                    # No aggressive type conversion needed here.
                    # json.dump will correctly handle Python's int, float, and str types.
                    # IDs are already converted to str earlier when constructing the item dictionaries.
                    json.dump(item, f)
                    f.write('\n') # Newline for each JSON object

        # Ensure we write to the 'backend/' directory as expected by inventory_service.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # We need to go up one level from `backend/` if `data_prep.py` is executed from project root
        # If data_prep.py is in backend/, then the paths are relative to backend/
        # Given the previous context, data_prep.py is in the root, so files go to data/ directory.
        # But `inventory_service.py` expects them in backend/.
        # Let's adjust for `data_prep.py` being in the project root and creating files in `data/` folder,
        # which means `inventory_service.py` will have to look into `../data/`
        # OR, we make `data_prep.py` write directly to `backend/`. Let's stick with the latter
        # for consistency with `inventory_service.py`'s current pathing.
        
        # The README says `data_prep.py` is in the root and json files are generated in `data/` folder.
        # `inventory_service.py` explicitly looks for them relative to `backend/`.
        # This implies `data_prep.py` should write them to `backend/` or `inventory_service.py` should change its path.
        # Let's align `data_prep.py` to write to `backend/` directly as that's where `inventory_service.py` expects it.
        backend_dir = os.path.join(current_dir) # Assuming data_prep.py is in backend/ as per last conversation
        # OR, if data_prep.py is in root, then backend_dir would be os.path.join(current_dir, 'backend')
        # Let's assume data_prep.py is in the root as per the README's overall structure,
        # and it should write the files into the `backend/` directory.

        # Re-evaluating path: README says data_prep.py is in root, but backend/db_client.py and backend/app.py use backend/ml_models.
        # This means data_prep.py should write to backend/.
        # So, if data_prep.py is truly in the root, the path below needs to be `os.path.join(current_dir, 'backend', filename)`
        # However, the previous path was `os.path.join(os.path.dirname(csv_path), 'products.json')` which would put it next to the CSV (root).
        # To match inventory_service's expectation (which assumes files are in backend/ alongside it, i.e., in its parent folder),
        # data_prep.py should write them to `backend/`.
        # Let's use `os.path.join(os.path.dirname(csv_path), 'backend', filename)` if data_prep.py is in root and csv_path points to root.
        # The last version of data_prep.py had `current_dir = os.path.dirname(os.path.abspath(__file__))` and `csv_file_path = os.path.join(current_dir, DATASET_PATH)`.
        # This means `DATASET_PATH` (`retail_inventory_forecast.csv`) is expected in the *same directory* as `data_prep.py`.
        # If `data_prep.py` is in the root, the csv is in the root. The json files are written to `os.path.dirname(csv_path)` which is the root.
        # But `inventory_service.py` expects them in `backend/`.
        # So, the write path needs to change.

        # Get the directory where this script (data_prep.py) is located.
        # This assumes data_prep.py is in the 'backend/' directory.
        output_dir = os.path.dirname(os.path.abspath(__file__)) 
        
        # Ensure the directory exists (it should, but good practice)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        write_ndjson(products_list, os.path.join(output_dir, 'products.json'))
        write_ndjson(stores_list, os.path.join(output_dir, 'stores.json'))
        write_ndjson(inventory_list, os.path.join(output_dir, 'inventory.json'))

        print(f"\nSuccessfully generated products.json, stores.json, and inventory.json in the {output_dir} directory.")
    except Exception as e:
        print(f"An error occurred during data preparation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Assuming data_prep.py is in the project root based on README structure
    current_root_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_root_dir, DATASET_PATH)
    prepare_firestore_data(csv_file_path)

