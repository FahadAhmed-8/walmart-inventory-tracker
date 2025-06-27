# backend/check_data.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
import urllib.parse

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI and database name from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "walmart_inventory_db")

def check_mongodb_data_locally():
    client = None
    try:
        if MONGO_URI is None:
            print("Error: MONGO_URI environment variable not set. Please check your .env file.")
            return

        print("Attempting to connect to MongoDB to verify data...")
        
        # Reconstruct the URI with URL-escaped credentials if they exist
        parsed_uri = urllib.parse.urlparse(MONGO_URI)
        username = parsed_uri.username
        password = parsed_uri.password
        
        if username and password:
            escaped_username = urllib.parse.quote_plus(username)
            escaped_password = urllib.parse.quote_plus(password)
            netloc_with_creds = f"{escaped_username}:{escaped_password}@{parsed_uri.hostname}"
            mongo_uri_escaped = parsed_uri._replace(netloc=netloc_with_creds).geturl()
        else:
            mongo_uri_escaped = MONGO_URI

        # Connect to MongoDB using certifi for SSL, keeping tlsAllowInvalidCertificates=True for consistency
        client = MongoClient(mongo_uri_escaped, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
        db = client[MONGO_DB_NAME]

        # Check if the 'products' collection exists and has documents
        if 'products' in db.list_collection_names():
            print("\n'products' collection found.")
            product_count = db.products.count_documents({})
            print(f"Number of documents in 'products' collection: {product_count}")

            # Fetch one product document to check for the new fields
            print("\nFetching a sample product document to inspect new fields:")
            sample_product = db.products.find_one({})
            if sample_product:
                print(f"Sample product details (first document):")
                print(f"  Product ID: {sample_product.get('product_id')}")
                print(f"  Category: {sample_product.get('category')}")
                print(f"  Price: {sample_product.get('price')}")
                print(f"  Name: {sample_product.get('name')}")
                print(f"  Min Replenish Time: {sample_product.get('min_replenish_time')}")
                
                # Check for the newly added fields
                if 'base_safety_stock' in sample_product and 'supplier_category_reliability' in sample_product:
                    print(f"  Base Safety Stock (NEW): {sample_product.get('base_safety_stock')}")
                    print(f"  Supplier Category Reliability (NEW): {sample_product.get('supplier_category_reliability')}")
                    print("\nSUCCESS: The new 'base_safety_stock' and 'supplier_category_reliability' fields are present and populated!")
                else:
                    print("\nWARNING: The new 'base_safety_stock' or 'supplier_category_reliability' fields are MISSING in the sample product.")
                    print("This might mean the data wasn't reloaded correctly. Consider manually dropping the 'products' collection in MongoDB Atlas and restarting the Flask app.")
            else:
                print("No documents found in the 'products' collection.")
        else:
            print("The 'products' collection does not exist in the database. Data might not have been loaded.")

    except Exception as e:
        print(f"An error occurred while trying to connect to MongoDB or fetch data: {e}")
    finally:
        if client:
            client.close()
            print("MongoDB connection closed.")

if __name__ == '__main__':
    check_mongodb_data_locally()
