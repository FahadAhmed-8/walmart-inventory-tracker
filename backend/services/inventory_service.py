# backend/services/inventory_service.py
import datetime
import os
import json
import time
import pandas as pd
import pymongo # Needed for pymongo.UpdateOne
from pymongo.errors import BulkWriteError, ConnectionFailure
from pymongo import ReturnDocument

# Paths to your pre-generated NDJSON files (relative to backend/ directory, where data_prep.py placed them)
PRODUCTS_JSON_PATH = 'products.json'
STORES_JSON_PATH = 'stores.json'
INVENTORY_JSON_PATH = 'inventory.json'

def load_initial_inventory_data(db):
    """
    Loads initial data from generated NDJSON files into MongoDB collections.
    This function is intended to be called once for initial data population.
    It includes aggressive rate limiting and basic retry logic.
    
    Args:
        db: The MongoDB database client instance.
    """
    if db is None:
        print("MongoDB database instance not provided. Cannot load initial data.")
        return

    # Adjust paths if data_prep.py places them elsewhere or if this script is run from a different CWD
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir) # Go up one level from services to backend
    
    products_file = os.path.join(backend_dir, PRODUCTS_JSON_PATH)
    stores_file = os.path.join(backend_dir, STORES_JSON_PATH)
    inventory_file = os.path.join(backend_dir, INVENTORY_JSON_PATH)

    if not (os.path.exists(products_file) and
            os.path.exists(stores_file) and
            os.path.exists(inventory_file)):
        print(f"Error: One or more NDJSON files not found at expected locations:")
        print(f" - Products: {products_file}")
        print(f" - Stores: {stores_file}")
        print(f" - Inventory: {inventory_file}")
        print("Please ensure they are in the backend/ directory and were generated by data_prep.py.")
        return

    print("Starting initial data load from NDJSON files into MongoDB...")
    
    collections_to_load = {
        'products': products_file,
        'stores': stores_file,
        'inventory': inventory_file,
    }

    # Configuration for rate limiting and retries
    max_batch_size = 100 # Smaller batch size for initial load
    delay_between_batches = 3.0 # Seconds to wait between batch inserts (increased for safety)
    max_retries = 5
    retry_delay_multiplier = 2 # Multiplier for exponential backoff on retry

    print(f"Delay between batches set to: {delay_between_batches} seconds")
    print(f"Max batch size set to: {max_batch_size} operations")

    for collection_name, file_path in collections_to_load.items():
        print(f"\n--- Loading {collection_name} collection from {file_path} ---")
        
        items_to_insert = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip(): # Avoid empty lines
                    item = json.loads(line)
                    # Prepare data for MongoDB insertion based on collection type
                    if collection_name == 'inventory':
                        # Ensure 'last_updated' is a datetime object
                        if 'last_updated' in item and isinstance(item['last_updated'], str):
                            try:
                                item['last_updated'] = datetime.datetime.fromisoformat(item['last_updated'])
                            except ValueError:
                                item['last_updated'] = datetime.datetime.now()
                        else:
                            item['last_updated'] = datetime.datetime.now()
                        # Ensure numerical fields are proper types, provide defaults
                        item['current_stock'] = int(item.get('current_stock', 0))
                        item['daily_sales_simulation_base'] = int(item.get('daily_sales_simulation_base', 1))

                    items_to_insert.append(item)
        
        print(f"Read {len(items_to_insert)} items for {collection_name}.")

        if not items_to_insert:
            print(f"No items to load for {collection_name}. Skipping.")
            continue

        current_collection = db[collection_name]
        
        # Drop the collection before inserting to ensure a clean slate on re-run (for development)
        # CAUTION: In production, you would NOT do this for existing data
        print(f"Dropping existing '{collection_name}' collection for clean import...")
        current_collection.drop()

        # Perform bulk inserts with rate limiting
        total_items_processed = 0
        for i in range(0, len(items_to_insert), max_batch_size):
            batch_data = items_to_insert[i:i + max_batch_size]
            
            retries = 0
            while retries < max_retries:
                try:
                    # Insert many documents at once
                    current_collection.insert_many(batch_data, ordered=False) # ordered=False continues on error
                    total_items_processed += len(batch_data)
                    print(f"  Inserted {len(batch_data)} {collection_name} records (Total: {total_items_processed}). Waiting {delay_between_batches}s...")
                    time.sleep(delay_between_batches)
                    break # Batch inserted successfully, break retry loop
                except BulkWriteError as bwe:
                    print(f"  BulkWriteError for {collection_name}: {bwe.details}")
                    # For a hackathon, we might just log and continue on BulkWriteError (e.g., duplicate key)
                    total_items_processed += bwe.details.get('nInserted', 0) # Count successful inserts in batch
                    print(f"  Partial batch inserted. Total: {total_items_processed}. Waiting {delay_between_batches}s...")
                    time.sleep(delay_between_batches)
                    break # Continue even on partial errors for now
                except ConnectionFailure as ce:
                    print(f"  MongoDB ConnectionFailure during insert for {collection_name}: {ce}")
                    retries += 1
                    current_retry_delay = delay_between_batches * (retry_delay_multiplier ** retries)
                    print(f"  Connection error. Retrying in {current_retry_delay}s... (Attempt {retries}/{max_retries})")
                    time.sleep(current_retry_delay)
                except Exception as e:
                    print(f"  Error inserting batch for {collection_name}: {e}")
                    retries += 1
                    current_retry_delay = delay_between_batches * (retry_delay_multiplier ** retries)
                    print(f"  General error. Retrying in {current_retry_delay}s... (Attempt {retries}/{max_retries})")
                    time.sleep(current_retry_delay)

            if retries == max_retries:
                print(f"  Failed to insert batch for {collection_name} after {max_retries} retries. Skipping remaining items in this batch.")

        # Ensure all items processed messages are printed for this collection even if batch_item_count is less than max_batch_size
        if total_items_processed < len(items_to_insert):
            print(f"  Note: Some items might have been skipped for {collection_name} due to errors.")
        
        print(f"Finished loading {collection_name}. Total {total_items_processed} items processed.")

    print("\n--- Initial data load process complete ---")

def get_inventory_item(db, store_id, product_id):
    """
    Retrieves the current stock level and details for a specific product
    at a given store.
    """
    inventory_item = db.inventory.find_one({
        'store_id': store_id,
        'product_id': product_id
    })
    if inventory_item:
        inventory_item['_id'] = str(inventory_item['_id']) # Convert ObjectId to string
        if 'last_updated' in inventory_item and isinstance(inventory_item['last_updated'], datetime.datetime):
            inventory_item['last_updated'] = inventory_item['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
    return inventory_item

def record_sale_transaction(db, store_id, product_id, quantity):
    """
    Records a sale event, decrementing the inventory level.
    Ensures sufficient stock before update.
    Returns the new stock level or raises ValueError.
    """
    result = db.inventory.find_one_and_update(
        {'store_id': store_id, 'product_id': product_id, 'current_stock': {'$gte': quantity}},
        {'$inc': {'current_stock': -quantity}, '$set': {'last_updated': datetime.datetime.now(), 'last_sold_quantity': quantity}},
        return_document=ReturnDocument.AFTER
    )
    if result:
        return result['current_stock']
    else:
        existing_item = db.inventory.find_one({'store_id': store_id, 'product_id': product_id})
        if existing_item:
            raise ValueError(f"Insufficient stock. Current: {existing_item['current_stock']}, Requested: {quantity}")
        else:
            raise ValueError(f"Inventory item not found for Product ID: {product_id} at Store ID: {store_id}")

def record_receipt_transaction(db, store_id, product_id, quantity):
    """
    Records a new stock receipt, incrementing the inventory level.
    Creates the entry if it doesn't exist (upsert).
    Returns the new stock level.
    """
    result = db.inventory.find_one_and_update(
        {'store_id': store_id, 'product_id': product_id},
        {'$inc': {'current_stock': quantity}, '$set': {'last_updated': datetime.datetime.now(), 'last_receipt_quantity': quantity}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    if result:
        return result['current_stock']
    else:
        # This case should be rare with upsert=True unless a different error occurs
        raise ValueError(f"Failed to record receipt for Product ID: {product_id} at Store ID: {store_id}")


def process_sales_batch_csv(db, csv_file_stream):
    """
    Processes a CSV stream for multiple sales events using bulk write operations.
    """
    df = pd.read_csv(csv_file_stream)
    df.columns = df.columns.str.strip()

    required_cols = ['store_id', 'product_id', 'quantity']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain 'store_id', 'product_id', and 'quantity' columns. Missing: {', '.join([col for col in required_cols if col not in df.columns])}")

    results = []
    batch_size = 50
    delay_between_batches = 0.2

    all_updates_to_perform = []

    for index, row in df.iterrows():
        store_id = str(row['store_id'])
        product_id = str(row['product_id'])
        try:
            quantity = int(row['quantity'])
            if quantity <= 0:
                results.append({"row": index + 1, "status": "failed", "error": "Quantity must be positive.", "store_id": store_id, "product_id": product_id})
                continue
        except ValueError:
            results.append({"row": index + 1, "status": "failed", "error": "Invalid quantity format.", "store_id": store_id, "product_id": product_id})
            continue

        all_updates_to_perform.append({
            'filter': {'store_id': store_id, 'product_id': product_id, 'current_stock': {'$gte': quantity}},
            'update': {'$inc': {'current_stock': -quantity}, '$set': {'last_updated': datetime.datetime.now(), 'last_sold_quantity': quantity}},
            'index': index + 1 # Store original row index for results
        })
    
    for i in range(0, len(all_updates_to_perform), batch_size):
        current_batch_updates = all_updates_to_perform[i:i + batch_size]
        
        bulk_write_requests = [
            pymongo.UpdateOne(op['filter'], op['update']) for op in current_batch_updates
        ]
        
        try:
            if bulk_write_requests:
                db.inventory.bulk_write(bulk_write_requests, ordered=False)
                for op_info in current_batch_updates:
                    results.append({
                        "row": op_info['index'],
                        "status": "success",
                        "message": "Processed in batch (stock checked)",
                        "store_id": op_info['filter']['store_id'],
                        "product_id": op_info['filter']['product_id']
                    })
            time.sleep(delay_between_batches)

        except BulkWriteError as bwe:
            print(f"  Partial success/error in batch sale: {bwe.details}")
            for op_info in current_batch_updates:
                results.append({
                    "row": op_info['index'],
                    "status": "partial_success/failure",
                    "message": "See backend logs for details",
                    "store_id": op_info['filter']['store_id'],
                    "product_id": op_info['filter']['product_id']
                })
            time.sleep(delay_between_batches)
        except Exception as e:
            print(f"  Error processing sale batch: {e}")
            for op_info in current_batch_updates:
                results.append({
                    "row": op_info['index'],
                    "status": "failed",
                    "error": str(e),
                    "store_id": op_info['filter']['store_id'],
                    "product_id": op_info['filter']['product_id']
                })
            time.sleep(delay_between_batches)
    
    return results

def process_receipts_batch_csv(db, csv_file_stream):
    """
    Processes a CSV stream for multiple receipt events using bulk write operations.
    """
    df = pd.read_csv(csv_file_stream)
    df.columns = df.columns.str.strip()

    required_cols = ['store_id', 'product_id', 'quantity']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain 'store_id', 'product_id', and 'quantity' columns. Missing: {', '.join([col for col in required_cols if col not in df.columns])}")

    results = []
    batch_size = 50
    delay_between_batches = 0.2
    
    all_updates_to_perform = []

    for index, row in df.iterrows():
        store_id = str(row['store_id'])
        product_id = str(row['product_id'])
        try:
            quantity = int(row['quantity'])
            if quantity <= 0:
                results.append({"row": index + 1, "status": "failed", "error": "Quantity must be positive.", "store_id": store_id, "product_id": product_id})
                continue
        except ValueError:
            results.append({"row": index + 1, "status": "failed", "error": "Invalid quantity format.", "store_id": store_id, "product_id": product_id})
            continue

        all_updates_to_perform.append({
            'filter': {'store_id': store_id, 'product_id': product_id},
            'update': {'$inc': {'current_stock': quantity}, '$set': {'last_updated': datetime.datetime.now(), 'last_receipt_quantity': quantity}},
            'upsert': True,
            'index': index + 1
        })
    
    for i in range(0, len(all_updates_to_perform), batch_size):
        current_batch_updates = all_updates_to_perform[i:i + batch_size]
        
        bulk_write_requests = [
            pymongo.UpdateOne(op['filter'], op['update'], upsert=op['upsert']) for op in current_batch_updates
        ]
        
        try:
            if bulk_write_requests:
                db.inventory.bulk_write(bulk_write_requests, ordered=False)
                for op_info in current_batch_updates:
                    results.append({
                        "row": op_info['index'],
                        "status": "success",
                        "message": "Processed in batch",
                        "store_id": op_info['filter']['store_id'],
                        "product_id": op_info['filter']['product_id']
                    })
            time.sleep(delay_between_batches)

        except BulkWriteError as bwe:
            print(f"  Partial success/error in batch receipt: {bwe.details}")
            for op_info in current_batch_updates:
                results.append({
                    "row": op_info['index'],
                    "status": "partial_success/failure",
                    "message": "See backend logs for details",
                    "store_id": op_info['filter']['store_id'],
                    "product_id": op_info['filter']['product_id']
                })
            time.sleep(delay_between_batches)
        except Exception as e:
            print(f"  Error processing receipt batch: {e}")
            for op_info in current_batch_updates:
                results.append({
                    "row": op_info['index'],
                    "status": "failed",
                    "error": str(e),
                    "store_id": op_info['filter']['store_id'],
                    "product_id": op_info['filter']['product_id']
                })
            time.sleep(delay_between_batches)
    
    return results

def get_low_stock_alerts_data(db, days_left_threshold, store_filter_id=None):
    """
    Identifies and returns products across all stores that are projected to run out
    within a specified number of `days_left`, based on their current stock and
    simulated daily sales. Also incorporates 'min_replenish_time' for advanced alerts.
    Results are sorted by 'days_remaining' in ascending order.
    """
    critical_stock_items = []
    
    query_filter = {}
    if store_filter_id:
        query_filter['store_id'] = store_filter_id

    # Fetch all products once to get their replenishment times
    products_collection = db['products']
    all_products = {}
    for product_doc in products_collection.find({}):
        all_products[product_doc['product_id']] = product_doc.get('min_replenish_time', 0) # Default to 0 if missing

    for item in db.inventory.find(query_filter):
        product_id = item.get('product_id')
        store_id = item.get('store_id')
        current_stock = item.get('current_stock', 0)
        daily_demand_sim = item.get('daily_sales_simulation_base', 1) 
        min_replenish_time = all_products.get(product_id, 0) # Get replenishment time for this product

        days_remaining = float('inf')
        if daily_demand_sim > 0:
            days_remaining = current_stock / daily_demand_sim
        elif current_stock == 0:
            days_remaining = 0.0

        alert_category = "Standard Alert"
        alert_reason = f"Projected to run out in {round(days_remaining, 2)} days (within {days_left_threshold} days limit)"

        if current_stock == 0:
            alert_category = "Critical - Out of Stock"
            alert_reason = "Currently out of stock."
        elif days_remaining <= min_replenish_time and days_remaining > 0:
            alert_category = "Critical - Below Replenishment Lead Time"
            alert_reason = f"Projected to run out in {round(days_remaining, 2)} days, which is less than replenishment time of {min_replenish_time} days."
        elif days_remaining <= days_left_threshold and days_remaining > 0:
            alert_category = "Warning - Approaching Threshold"
            alert_reason = f"Projected to run out in {round(days_remaining, 2)} days (within {days_left_threshold} days limit)."
        else: # If stock is sufficient and not critical, we don't add to alerts list
            continue


        # Only add to alerts list if it matches one of our alert conditions
        if alert_category != "Standard Alert":
            if 'last_updated' in item and isinstance(item['last_updated'], datetime.datetime):
                item['last_updated'] = item['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            
            alert_info = {
                "product_id": product_id,
                "store_id": store_id,
                "current_stock": current_stock,
                "daily_demand_sim": daily_demand_sim,
                "min_replenish_time": min_replenish_time,
                "days_remaining": round(days_remaining, 2),
                "alert_category": alert_category,
                "alert_reason": alert_reason,
                "last_updated": item.get('last_updated')
            }
            critical_stock_items.append(alert_info)

    # Sort the alerts by 'days_remaining' in ascending order
    critical_stock_items.sort(key=lambda x: x['days_remaining'])

    return critical_stock_items

def get_overstocked_products_data(db, threshold_multiplier, days_for_demand, store_filter_id=None):
    """
    Identifies and returns products across all stores that are considered overstocked.
    An item is overstocked if its current stock is greater than
    (threshold_multiplier * (daily_sales_simulation_base * days_for_demand)).

    Args:
        db: The MongoDB database client instance.
        threshold_multiplier (float): Multiplier for projected demand (e.g., 3.0 for 3x demand).
        days_for_demand (int): Number of days to project demand for.
        store_filter_id (str, optional): Filters alerts for a specific store.
    """
    overstocked_items = []

    query_filter = {}
    if store_filter_id:
        query_filter['store_id'] = store_filter_id

    # Fetch product names for a more descriptive alert
    products_collection = db['products']
    all_products_names = {}
    for product_doc in products_collection.find({}):
        all_products_names[product_doc['product_id']] = product_doc.get('name', 'Unknown Product')

    for item in db.inventory.find(query_filter):
        product_id = item.get('product_id')
        store_id = item.get('store_id')
        current_stock = item.get('current_stock', 0)
        daily_demand_sim = item.get('daily_sales_simulation_base', 1)

        projected_demand = daily_demand_sim * days_for_demand
        
        # Check for overstocked condition
        if projected_demand > 0 and current_stock > (threshold_multiplier * projected_demand):
            # Convert ObjectId to string and datetime to string for JSON serialization
            item['_id'] = str(item['_id'])
            if 'last_updated' in item and isinstance(item['last_updated'], datetime.datetime):
                item['last_updated'] = item['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
            
            overstock_info = {
                "product_id": product_id,
                "product_name": all_products_names.get(product_id, f"Product {product_id}"),
                "store_id": store_id,
                "current_stock": current_stock,
                "daily_demand_sim": daily_demand_sim,
                "projected_demand_for_X_days": round(projected_demand, 2),
                "threshold_multiplier": threshold_multiplier,
                "overstock_ratio": round(current_stock / projected_demand, 2) if projected_demand > 0 else "N/A",
                "alert_reason": (
                    f"Current stock ({current_stock}) is {round(current_stock / projected_demand, 2) if projected_demand > 0 else 'N/A'} times "
                    f"the projected demand of {round(projected_demand, 2)} units over {days_for_demand} days "
                    f"(threshold: {threshold_multiplier}x)."
                ),
                "last_updated": item.get('last_updated')
            }
            overstocked_items.append(overstock_info)

    # Sort overstocked items by overstock_ratio descending (most overstocked first)
    overstocked_items.sort(key=lambda x: x.get('overstock_ratio', 0) if isinstance(x.get('overstock_ratio'), (int, float)) else 0, reverse=True)

    return overstocked_items

def get_demand_forecast_data_ml(db, ml_model, preprocessor, numerical_features, categorical_features, store_id, product_id, num_days=30, **kwargs):
    """
    Generates a demand forecast for a specific product at a given store for future days
    using the loaded machine learning model and preprocessor. Allows for 'what-if' scenario inputs.

    Args:
        db: MongoDB database instance.
        ml_model: The pre-trained machine learning model.
        preprocessor: The pre-trained ColumnTransformer for feature preprocessing.
        numerical_features: List of numerical feature names used during training.
        categorical_features: List of categorical feature names used during training.
        store_id (str): The ID of the store for which to forecast.
        product_id (str): The ID of the product for which to forecast.
        num_days (int): Number of future days to forecast.
        **kwargs: Optional 'what-if' parameters (e.g., 'future_discount', 'future_holiday').
    """
    if ml_model is None or preprocessor is None:
        raise ValueError("ML model or preprocessor not loaded in the backend.")

    inventory_record = db.inventory.find_one(
        {'store_id': store_id, 'product_id': product_id},
        sort=[('last_updated', pymongo.DESCENDING)]
    )
    if not inventory_record:
        raise ValueError(f"Inventory record not found for Product ID: {product_id} at Store ID: {store_id}.")
    
    product_details = db.products.find_one({'product_id': product_id})
    if not product_details:
        raise ValueError(f"Product details not found for Product ID: {product_id}.")

    store_details = db.stores.find_one({'store_id': store_id})
    if not store_details:
        raise ValueError(f"Store details not found for Store ID: {store_id}.")

    last_units_sold = inventory_record.get('last_sold_quantity', 0)
    last_inventory_level = inventory_record.get('current_stock', 0)
    
    avg_price = 10.0
    avg_discount = 0.0

    try:
        product_pricing = db.products.find_one(
            {"product_id": product_id},
            {"price": 1, "discount": 1, "_id": 0}
        )
        if product_pricing:
            if product_pricing.get('price') is not None:
                avg_price = float(product_pricing['price'])
            if product_pricing.get('discount') is not None:
                avg_discount = float(product_pricing['discount'])
        else: 
            try:
                avg_price_doc = db.products.aggregate([{"$group": {"_id": None, "avg_price": {"$avg": "$price"}}}]).next()
                if avg_price_doc and avg_price_doc.get('avg_price') is not None:
                    avg_price = float(avg_price_doc['avg_price'])
            except StopIteration:
                pass
            
            try:
                avg_discount_doc = db.products.aggregate([{"$group": {"_id": None, "avg_discount": {"$avg": "$discount"}}}]).next()
                if avg_discount_doc and avg_discount_doc.get('avg_discount') is not None:
                    avg_discount = float(avg_discount_doc['avg_discount'])
            except StopIteration:
                pass
    except Exception as e:
        print(f"Warning: Could not robustly calculate price/discount for product {product_id}: {e}. Using defaults.")

    units_ordered_future = 0 
    competitor_pricing_default = avg_price * 0.95 
    
    forecast_data = []
    current_date = datetime.date.today()

    # Use kwargs for 'what-if' values, or fall back to defaults
    future_discount_override = kwargs.get('future_discount', avg_discount)
    future_holiday_override = kwargs.get('future_holiday', "No")
    future_weather_override = kwargs.get('future_weather', "Clear") # Default to clear
    future_price_override = kwargs.get('future_price', avg_price)
    future_competitor_pricing_override = kwargs.get('future_competitor_pricing', competitor_pricing_default)


    for i in range(num_days):
        forecast_date = current_date + datetime.timedelta(days=i)
        
        # Apply overrides from what-if scenarios, otherwise use defaults
        weather_condition = future_weather_override
        holiday_promotion = future_holiday_override
        price_for_forecast = future_price_override
        discount_for_forecast = future_discount_override
        competitor_pricing_for_forecast = future_competitor_pricing_override

        month = forecast_date.month
        seasonality = "Spring" if 3 <= month <= 5 else \
                      "Summer" if 6 <= month <= 8 else \
                      "Autumn" if 9 <= month <= 11 else \
                      "Winter" 
        
        future_data_row_dict = {
            'Date': forecast_date, 
            'Store ID': store_id,
            'Product ID': product_id,
            'Category': product_details.get('category', 'Unknown'),
            'Region': store_details.get('region', 'Unknown'),
            'Inventory Level': last_inventory_level,
            'Units Ordered': units_ordered_future,
            'Price': price_for_forecast,
            'Discount': discount_for_forecast,
            'Weather Condition': weather_condition,
            'Holiday/Promotion': holiday_promotion,
            'Competitor Pricing': competitor_pricing_for_forecast,
            'Seasonality': seasonality,
            'Units Sold Lag1': last_units_sold, 
            'Inventory Level Lag1': last_inventory_level 
        }

        future_data_df = pd.DataFrame([future_data_row_dict])
        future_data_df['Date'] = pd.to_datetime(future_data_df['Date'])
        
        future_data_df['Year'] = future_data_df['Date'].dt.year
        future_data_df['Month'] = future_data_df['Date'].dt.month
        future_data_df['Day'] = future_data_df['Date'].dt.day
        future_data_df['DayOfWeek'] = future_data_df['Date'].dt.dayofweek
        future_data_df['WeekOfYear'] = future_data_df['Date'].dt.isocalendar().week.astype(int)

        all_expected_features_for_df = numerical_features + categorical_features

        X_forecast_input = pd.DataFrame(columns=all_expected_features_for_df)
        for col in all_expected_features_for_df:
            if col in future_data_df.columns:
                X_forecast_input[col] = future_data_df[col]
            else:
                if col in numerical_features:
                    X_forecast_input[col] = 0.0 
                elif col in categorical_features:
                    X_forecast_input[col] = 'Unknown'
                else:
                    X_forecast_input[col] = 'NaN' 

        X_forecast_processed = preprocessor.transform(X_forecast_input)

        predicted_demand = ml_model.predict(X_forecast_processed)[0]
        predicted_demand = max(0, round(predicted_demand)) 

        forecast_data.append({
            "date": forecast_date.isoformat(),
            "predicted_demand": predicted_demand,
            "store_id": store_id,
            "product_id": product_id
        })
        
        last_units_sold = predicted_demand 

    return forecast_data


def get_reorder_recommendation(db, ml_model, preprocessor, numerical_features, categorical_features, store_id, product_id):
    """
    Calculates reorder recommendations (quantity, order date, delivery date)
    based on current stock, product lead time, and forecasted demand.
    """
    inventory_record = db.inventory.find_one(
        {'store_id': store_id, 'product_id': product_id}
    )
    if not inventory_record:
        raise ValueError(f"Inventory record not found for Product ID: {product_id} at Store ID: {store_id}.")
    
    product_details = db.products.find_one({'product_id': product_id})
    if not product_details:
        raise ValueError(f"Product details not found for Product ID: {product_id}.")

    current_stock = inventory_record.get('current_stock', 0)
    # Default replenishment time to 7 days if not found in product details
    min_replenish_time = product_details.get('min_replenish_time', 7) 
    
    # Define safety stock days (e.g., 7 days of forecasted demand)
    SAFETY_STOCK_DAYS = 7 
    # Define target inventory days (e.g., maintain 30 days of stock after replenishment)
    TARGET_INVENTORY_DAYS = 30

    # 1. Get demand forecast for lead time + safety stock days
    # We need forecast for `min_replenish_time + SAFETY_STOCK_DAYS` days to calculate total demand until reorder point
    # We'll use the ML-driven forecast.
    total_forecast_days_needed = min_replenish_time + SAFETY_STOCK_DAYS
    
    # Ensure num_days is at least 1 for forecast function
    if total_forecast_days_needed <= 0:
        total_forecast_days_needed = 1 

    forecast_for_lead_time_and_safety = get_demand_forecast_data_ml(
        db, ml_model, preprocessor, numerical_features, categorical_features, 
        store_id, product_id, num_days=total_forecast_days_needed
    )
    
    # Calculate total forecasted demand over the period
    total_forecasted_demand = sum([f['predicted_demand'] for f in forecast_for_lead_time_and_safety])

    # Calculate average daily forecasted demand over the period for safety stock calculation
    average_daily_forecasted_demand = total_forecasted_demand / total_forecast_days_needed if total_forecast_days_needed > 0 else inventory_record.get('daily_sales_simulation_base', 1)

    # Calculate Safety Stock (e.g., 7 days of average forecasted demand)
    safety_stock_units = round(average_daily_forecasted_demand * SAFETY_STOCK_DAYS)

    # Calculate Reorder Point: Demand during lead time + Safety Stock
    # For demand during lead time, use forecast specifically for lead time days
    demand_during_lead_time = sum([f['predicted_demand'] for f in forecast_for_lead_time_and_safety[:min_replenish_time]])
    reorder_point = max(0, round(demand_during_lead_time + safety_stock_units)) # Ensure non-negative

    # Suggested Order Quantity: Quantity to bring stock up to TARGET_INVENTORY_DAYS + Safety Stock
    # Calculate total demand for target inventory days
    forecast_for_target_inventory = get_demand_forecast_data_ml(
        db, ml_model, preprocessor, numerical_features, categorical_features, 
        store_id, product_id, num_days=TARGET_INVENTORY_DAYS
    )
    total_forecasted_demand_target = sum([f['predicted_demand'] for f in forecast_for_target_inventory])

    target_inventory_level = total_forecasted_demand_target + safety_stock_units
    
    suggested_order_quantity = max(0, round(target_inventory_level - current_stock))
    
    # If current stock is already very high (above reorder point and target), suggest 0 or very small
    if current_stock > reorder_point and suggested_order_quantity <= 0:
        suggested_order_quantity = 0

    # Calculate Order Date and Delivery Date
    order_date = datetime.date.today()
    delivery_date = order_date + datetime.timedelta(days=min_replenish_time)

    # Determine if a reorder is currently needed
    reorder_needed = "Yes" if current_stock <= reorder_point and suggested_order_quantity > 0 else "No"
    
    return {
        "store_id": store_id,
        "product_id": product_id,
        "current_stock": current_stock,
        "min_replenish_time_days": min_replenish_time,
        "average_daily_forecasted_demand": round(average_daily_forecasted_demand, 2),
        "safety_stock_units": safety_stock_units,
        "reorder_point_units": reorder_point,
        "reorder_needed": reorder_needed,
        "suggested_order_quantity": suggested_order_quantity,
        "suggested_order_date": order_date.isoformat(),
        "suggested_delivery_date": delivery_date.isoformat(),
        "notes": "Recommendation based on ML demand forecast, lead time, and safety stock. Adjust parameters as needed."
    }

