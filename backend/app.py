# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import io # For CSV file handling
import pandas as pd # Needed for batch CSV processing in routes
import datetime # Needed for timestamp handling if CSV parsing happens here
import joblib # For saving/loading models
import os # For pathing to ML models
import sys # NEW: Import sys to access command-line arguments

# Import MongoDB client functions
from db_client import get_db, connect_to_mongodb

# Import inventory service functions
from services.inventory_service import (
    load_initial_inventory_data,
    get_inventory_item,
    record_sale_transaction,
    record_receipt_transaction,
    process_sales_batch_csv,
    process_receipts_batch_csv,
    get_low_stock_alerts_data,
    get_overstocked_products_data,
    get_demand_forecast_data_ml, # Re-import the updated ML-driven forecast function
    get_reorder_recommendation, # NEW: Import reorder recommendation function
    get_optimal_stocking_data,
    get_remediation_actions # NEW: Import the new function
)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Load ML Model and Preprocessor at App Startup ---
MODELS_DIR = 'ml_models'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

best_model_filename = None
for f in os.listdir(os.path.join(CURRENT_DIR, MODELS_DIR)):
    if f.startswith('best_demand_forecast_model_') and f.endswith('.joblib'):
        best_model_filename = f
        break

GLOBAL_ML_MODEL = None
GLOBAL_PREPROCESSOR = None
GLOBAL_NUMERICAL_FEATURES = []
GLOBAL_CATEGORICAL_FEATURES = []

if best_model_filename:
    MODEL_PATH = os.path.join(CURRENT_DIR, MODELS_DIR, best_model_filename)
    PREPROCESSOR_PATH = os.path.join(CURRENT_DIR, MODELS_DIR, 'feature_preprocessor.joblib')
    NUM_FEATURES_PATH = os.path.join(CURRENT_DIR, MODELS_DIR, 'numerical_features.joblib')
    CAT_FEATURES_PATH = os.path.join(CURRENT_DIR, MODELS_DIR, 'categorical_features.joblib')

    try:
        GLOBAL_ML_MODEL = joblib.load(MODEL_PATH)
        GLOBAL_PREPROCESSOR = joblib.load(PREPROCESSOR_PATH)
        GLOBAL_NUMERICAL_FEATURES = joblib.load(NUM_FEATURES_PATH)
        GLOBAL_CATEGORICAL_FEATURES = joblib.load(CAT_FEATURES_PATH)
        print(f"ML Model ({best_model_filename}), Preprocessor, and Feature lists loaded successfully.")
    except Exception as e:
        print(f"Error loading ML model components: {e}. Forecasting and Reorder APIs might not function.")
else:
    print("No best model file found in ml_models directory. Forecasting and Reorder APIs will not function.")


# --- API Endpoints ---

@app.route('/')
def home():
    """
    A simple home route to confirm the backend is running.
    """
    return "Walmart Inventory Management Backend is running! Access /inventory, /inventory/sale, /inventory/receipt, /inventory/low_stock_alerts, /inventory/overstocked_alerts, /inventory/forecast, /inventory/reorder_recommendation."

@app.route('/inventory/<string:store_id>/<string:product_id>', methods=['GET'])
def get_inventory(store_id, product_id):
    """
    Retrieves the current stock level and details for a specific product
    at a given store.
    """
    try:
        db = get_db()
        inventory_item = get_inventory_item(db, store_id, product_id)

        if inventory_item:
            return jsonify(inventory_item), 200
        else:
            return jsonify({"message": f"Inventory not found for Product ID: {product_id} at Store ID: {store_id}"}), 404
    except Exception as e:
        print(f"Error fetching inventory: {e}")
        return jsonify({"error": f"An error occurred while fetching inventory: {str(e)}"}), 500

@app.route('/inventory/sale', methods=['POST'])
def record_sale():
    """
    Records a sale event, decrementing the inventory level for a product
    at a specific store.
    """
    data = request.get_json()
    store_id = data.get('store_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not all([store_id, product_id, quantity is not None]):
        return jsonify({"error": "Missing 'store_id', 'product_id', or 'quantity' in request body."}), 400
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer."}), 400

    try:
        db = get_db()
        new_stock_level = record_sale_transaction(db, store_id, product_id, quantity)

        return jsonify({
            "message": "Sale recorded successfully",
            "product_id": product_id,
            "store_id": store_id,
            "quantity_sold": quantity,
            "new_stock_level": new_stock_level
        }), 200
    except ValueError as ve:
        print(f"Validation error recording sale: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Unexpected error recording sale: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/inventory/sale_batch', methods=['POST'])
def record_sale_batch():
    """
    Records multiple sales events from a CSV file.
    """
    try:
        db = get_db()
    except Exception as e:
        return jsonify({"error": f"Database connection error: {e}"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            # Pass the file stream directly to the service function
            results = process_sales_batch_csv(db, io.StringIO(file.stream.read().decode("UTF8")))
            return jsonify({"message": "Batch sale processing complete", "results": results}), 200
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            return jsonify({"error": f"Error processing CSV file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file format. Please upload a CSV file."}), 400


@app.route('/inventory/receipt', methods=['POST'])
def record_receipt():
    """
    Records a new stock receipt, incrementing the inventory level for a product
    at a specific store.
    """
    data = request.get_json()
    store_id = data.get('store_id')
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    if not all([store_id, product_id, quantity is not None]):
        return jsonify({"error": "Missing 'store_id', 'product_id', or 'quantity' in request body."}), 400
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer."}), 400

    try:
        db = get_db()
        new_stock_level = record_receipt_transaction(db, store_id, product_id, quantity)

        return jsonify({
            "message": "Receipt recorded successfully",
            "product_id": product_id,
            "store_id": store_id,
            "quantity_received": quantity,
            "new_stock_level": new_stock_level
        }), 200
    except ValueError as ve:
        print(f"Validation error recording receipt: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Unexpected error recording receipt: {e}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/inventory/receipt_batch', methods=['POST'])
def record_receipt_batch():
    """
    Records multiple receipt events from a CSV file.
    """
    try:
        db = get_db()
    except Exception as e:
        return jsonify({"error": f"Database connection error: {e}"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            # Pass the file stream directly to the service function
            results = process_receipts_batch_csv(db, io.StringIO(file.stream.read().decode("UTF8")))
            return jsonify({"message": "Batch receipt processing complete", "results": results}), 200
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            return jsonify({"error": f"Error processing CSV file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file format. Please upload a CSV file."}), 400


@app.route('/inventory/low_stock_alerts', methods=['GET'])
def get_low_stock_alerts():
    """
    Identifies and returns products across all stores that are projected to run out
    within a specified number of `days_left`, based on their current stock and
    simulated daily sales.
    """
    days_left_str = request.args.get('days_left', '7')
    store_filter_id = request.args.get('store_id')

    try:
        days_left_threshold = int(days_left_str)
        if days_left_threshold < 0:
            return jsonify({"error": "days_left must be a non-negative integer."}), 400
    except ValueError:
        return jsonify({"error": "Invalid 'days_left' value. Must be an integer."}), 400

    try:
        db = get_db()
        critical_stock_items = get_low_stock_alerts_data(db, days_left_threshold, store_filter_id)
        return jsonify(critical_stock_items), 200
    except Exception as e:
        print(f"Error fetching low stock alerts based on days: {e}")
        return jsonify({"error": f"An error occurred while fetching alerts: {str(e)}"}), 500

@app.route('/inventory/overstocked_alerts', methods=['GET'])
def get_overstocked_alerts():
    """
    Identifies and returns products across all stores that are considered overstocked.
    
    Query Parameters:
    - `threshold_multiplier`: Float, e.g., 3.0 for 3x demand (default: 3.0).
    - `days_for_demand`: Integer, number of days to project demand for (default: 30).
    - `store_id` (optional): Filter alerts for a specific store.
    """
    threshold_multiplier_str = request.args.get('threshold_multiplier', '3.0')
    days_for_demand_str = request.args.get('days_for_demand', '30')
    store_filter_id = request.args.get('store_id')

    try:
        threshold_multiplier = float(threshold_multiplier_str)
        days_for_demand = int(days_for_demand_str)
        if threshold_multiplier <= 0 or days_for_demand <= 0:
            return jsonify({"error": "threshold_multiplier and days_for_demand must be positive values."}), 400
    except ValueError:
        return jsonify({"error": "Invalid 'threshold_multiplier' or 'days_for_demand' value."}), 400

    try:
        db = get_db()
        overstocked_items = get_overstocked_products_data(db, threshold_multiplier, days_for_demand, store_filter_id)
        return jsonify(overstocked_items), 200
    except Exception as e:
        print(f"Error fetching overstocked alerts: {e}")
        return jsonify({"error": f"An error occurred while fetching overstocked alerts: {str(e)}"}), 500

@app.route('/inventory/forecast', methods=['GET'])
def get_demand_forecast():
    """
    Retrieves demand forecast for a specific product at a given store for future days.
    
    Query Parameters:
    - `store_id`: Required.
    - `product_id`: Required.
    - `num_days`: Integer, number of days to forecast (default: 30).
    - Optional 'what-if' parameters: `future_discount`, `future_holiday`, `future_weather`, `future_price`, `future_competitor_pricing`.
    """
    store_id = request.args.get('store_id')
    product_id = request.args.get('product_id')
    num_days_str = request.args.get('num_days', '30')

    # Collect optional 'what-if' parameters
    what_if_params = {
        'future_discount': request.args.get('future_discount'),
        'future_holiday': request.args.get('future_holiday'),
        'future_weather': request.args.get('future_weather'),
        'future_price': request.args.get('future_price'),
        'future_competitor_pricing': request.args.get('future_competitor_pricing')
    }
    # Convert numerical what-if params to float if they exist
    if what_if_params['future_discount'] is not None:
        try:
            what_if_params['future_discount'] = float(what_if_params['future_discount'])
        except ValueError:
            return jsonify({"error": "Invalid 'future_discount' value."}), 400
    if what_if_params['future_price'] is not None:
        try:
            what_if_params['future_price'] = float(what_if_params['future_price'])
        except ValueError:
            return jsonify({"error": "Invalid 'future_price' value."}), 400
    if what_if_params['future_competitor_pricing'] is not None:
        try:
            what_if_params['future_competitor_pricing'] = float(what_if_params['future_competitor_pricing'])
        except ValueError:
            return jsonify({"error": "Invalid 'future_competitor_pricing' value."}), 400
    
    # Filter out None values from what_if_params to pass only provided overrides
    what_if_params_filtered = {k: v for k, v in what_if_params.items() if v is not None}


    if not store_id or not product_id:
        return jsonify({"error": "Missing 'store_id' or 'product_id' for forecast."}), 400

    try:
        num_days = int(num_days_str)
        if num_days <= 0:
            return jsonify({"error": "num_days must be a positive integer."}), 400
    except ValueError:
        return jsonify({"error": "Invalid 'num_days' value. Must be an integer."}), 400

    if GLOBAL_ML_MODEL is None or GLOBAL_PREPROCESSOR is None:
        return jsonify({"error": "ML model or preprocessor not loaded. Cannot generate forecast."}), 500

    try:
        db = get_db()
        forecast_data = get_demand_forecast_data_ml(
            db, 
            GLOBAL_ML_MODEL, 
            GLOBAL_PREPROCESSOR, 
            GLOBAL_NUMERICAL_FEATURES, 
            GLOBAL_CATEGORICAL_FEATURES, 
            store_id, 
            product_id, 
            num_days,
            **what_if_params_filtered # Pass filtered what-if parameters
        )
        return jsonify(forecast_data), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error generating demand forecast: {e}")
        return jsonify({"error": f"An unexpected error occurred during forecasting: {str(e)}"}), 500


@app.route('/inventory/reorder_recommendation', methods=['GET']) # NEW ENDPOINT
def get_reorder_recommendations_api():
    """
    Provides reorder recommendations (suggested quantity, order date, delivery date)
    for a specific product at a given store.
    
    Query Parameters:
    - `store_id`: Required.
    - `product_id`: Required.
    """
    store_id = request.args.get('store_id')
    product_id = request.args.get('product_id')

    if not store_id or not product_id:
        return jsonify({"error": "Missing 'store_id' or 'product_id' for reorder recommendation."}), 400
    
    if GLOBAL_ML_MODEL is None or GLOBAL_PREPROCESSOR is None:
        return jsonify({"error": "ML model or preprocessor not loaded. Cannot generate reorder recommendation."}), 500

    try:
        db = get_db()
        recommendation = get_reorder_recommendation(
            db,
            GLOBAL_ML_MODEL,
            GLOBAL_PREPROCESSOR,
            GLOBAL_NUMERICAL_FEATURES,
            GLOBAL_CATEGORICAL_FEATURES,
            store_id,
            product_id
        )
        return jsonify(recommendation), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error generating reorder recommendation: {e}")
        return jsonify({"error": f"An unexpected error occurred during reorder recommendation: {str(e)}"}), 500

@app.route('/inventory/optimal_stocking', methods=['GET']) # NEW ENDPOINT
def get_optimal_stocking_api():
    """
    Provides optimal stocking level recommendations for a specific product at a given store.

    Query Parameters:
    - `store_id`: Required.
    - `product_id`: Required.
    """
    store_id = request.args.get('store_id')
    product_id = request.args.get('product_id')

    if not store_id or not product_id:
        return jsonify({"error": "Missing 'store_id' or 'product_id' for optimal stocking calculation."}), 400

    if GLOBAL_ML_MODEL is None or GLOBAL_PREPROCESSOR is None:
        return jsonify({"error": "ML model or preprocessor not loaded. Cannot calculate optimal stocking."}), 500

    try:
        db = get_db()
        optimal_stock_data = get_optimal_stocking_data(
            db,
            GLOBAL_ML_MODEL,
            GLOBAL_PREPROCESSOR,
            GLOBAL_NUMERICAL_FEATURES,
            GLOBAL_CATEGORICAL_FEATURES,
            store_id,
            product_id
        )
        return jsonify(optimal_stock_data), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error generating optimal stocking recommendation: {e}")
        return jsonify({"error": f"An unexpected error occurred during optimal stocking calculation: {str(e)}"}), 500

@app.route('/inventory/remediation_actions', methods=['GET']) # NEW ENDPOINT
def get_remediation_actions_api():
    """
    Retrieves a prioritized list of suggested remediation actions (order/promote)
    for understocked or overstocked products.

    Query Parameters (optional):
    - `store_id`: Filter actions for a specific store.
    - `product_id`: Filter actions for a specific product.
    """
    store_id = request.args.get('store_id')
    product_id = request.args.get('product_id')

    if GLOBAL_ML_MODEL is None or GLOBAL_PREPROCESSOR is None:
        return jsonify({"error": "ML model or preprocessor not loaded. Cannot generate remediation actions."}), 500

    try:
        db = get_db()
        remediation_actions = get_remediation_actions(
            db,
            GLOBAL_ML_MODEL,
            GLOBAL_PREPROCESSOR,
            GLOBAL_NUMERICAL_FEATURES,
            GLOBAL_CATEGORICAL_FEATURES,
            store_id_filter=store_id, # Pass optional filters
            product_id_filter=product_id # Pass optional filters
        )
        return jsonify(remediation_actions), 200
    except Exception as e:
        print(f"Error generating remediation actions: {e}")
        return jsonify({"error": f"An unexpected error occurred during remediation action calculation: {str(e)}"}), 500

# --- Running the Flask Application ---
if __name__ == '__main__':
    # Check for a command-line argument to force database reload
    force_db_reload = '--force-db-reload' in sys.argv

    try:
        db_instance = connect_to_mongodb() # Get the connected DB instance
        
        if force_db_reload:
            print("Force DB reload requested. Dropping existing collections and loading initial data...")
            # The load_initial_inventory_data function itself handles dropping existing collections
            load_initial_inventory_data(db_instance) 
            print("Forced initial data load completed.")
        elif db_instance.inventory.count_documents({}) == 0:
            print("Database appears empty. Starting initial data load...")
            load_initial_inventory_data(db_instance) # Load data using the connected DB instance
            print("Initial data load completed.")
        else:
            print("Database already contains data. Skipping initial data load.")

    except Exception as e:
        print(f"Application startup aborted due to MongoDB connection error or initial data load error: {e}")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5000)