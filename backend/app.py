# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import io # For CSV file handling
import pandas as pd # Needed for batch CSV processing in routes
import datetime # Needed for timestamp handling if CSV parsing happens here

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
    get_low_stock_alerts_data
)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- API Endpoints ---

@app.route('/')
def home():
    """
    A simple home route to confirm the backend is running.
    """
    return "Walmart Inventory Management Backend is running! Access /inventory, /inventory/sale, /inventory/receipt, /inventory/low_stock_alerts."

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

# --- Running the Flask Application ---
if __name__ == '__main__':
    # Ensure MongoDB connection is established before starting the Flask app
    # This will attempt to connect, and if it fails, the app won't start.
    try:
        connect_to_mongodb()
    except Exception as e:
        print(f"Application startup aborted due to MongoDB connection error: {e}")
        exit(1) # Exit if cannot connect to DB

    # IMPORTANT: load_initial_inventory_data() from services should ONLY be uncommented ONCE
    # for initial data loading (if you re-created backend folder entirely).
    # After successful load, keep it commented out.
    # load_initial_inventory_data(get_db()) # <-- UNCOMMENT THIS ONLY IF YOU NEED TO RELOAD DATA
    
    app.run(debug=True, host='0.0.0.0', port=5000)
