# backend/data_prep.py
import pandas as pd
import json
import datetime
import os
import random # NEW: Import random for generating replenishment time

# Path to your downloaded Kaggle dataset: "Retail Store Inventory Forecasting Dataset"
# This file should be in the same directory as this script.
DATASET_PATH = 'retail_inventory_forecast.csv'

def prepare_firestore_data(csv_path):
    """
    Reads the retail inventory CSV, processes it, and generates
    NDJSON files suitable for MongoDB (and Firestore) import.
    Generates 'inventory.json', 'products.json', and 'stores.json' locally.
    Adds a random 'min_replenish_time' to products.
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

        # --- Prepare Products Data ---
        products_data = {}
        for _, row in df.iterrows():
            product_id = str(row['Product ID'])
            if product_id not in products_data:
                products_data[product_id] = {
                    'product_id': product_id,
                    'category': row['Category'],
                    'price': float(row['Price']),
                    'name': f"Product {product_id}", # Mock name
                    'min_replenish_time': random.randint(3, 20) # NEW: Random replenishment time (3-20 days)
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

        # --- Write to NDJSON files ---
        def write_ndjson(data_list, filename):
            with open(filename, 'w') as f:
                for item in data_list:
                    # Convert IDs to string for consistency if they might be numbers initially
                    item_copy = {k: str(v) if isinstance(v, (int, float)) and ('id' in k.lower() or 'stock' in k.lower() or 'price' in k.lower() or 'quantity' in k.lower()) else v for k, v in item.items()}
                    json.dump(item_copy, f)
                    f.write('\n') # Newline for each JSON object

        write_ndjson(products_list, os.path.join(os.path.dirname(csv_path), 'products.json'))
        write_ndjson(stores_list, os.path.join(os.path.dirname(csv_path), 'stores.json'))
        write_ndjson(inventory_list, os.path.join(os.path.dirname(csv_path), 'inventory.json'))

        print("\nSuccessfully generated products.json, stores.json, and inventory.json in the backend/ directory.")
        
    except Exception as e:
        print(f"An error occurred during data preparation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, DATASET_PATH)
    prepare_firestore_data(csv_file_path)
