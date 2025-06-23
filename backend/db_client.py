# backend/db_client.py
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import urllib.parse  # Import urllib.parse for URL escaping

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI and database name from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "walmart_inventory_db")  # Default if not set

client = None
db = None

def connect_to_mongodb():
    """
    Establishes a connection to MongoDB Atlas.
    Handles URL escaping for password in the connection string.
    """
    global client, db
    if client is not None and db is not None:
        return db

    if MONGO_URI is None:
        raise ValueError("MONGO_URI environment variable not set. Please check your .env file.")

    try:
        print("Connecting to MongoDB Atlas...")

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

        client = MongoClient(mongo_uri_escaped)
        client.admin.command('ping')

        db = client[MONGO_DB_NAME]
        print(f"Successfully connected to MongoDB database: {MONGO_DB_NAME}")
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

def get_db():
    """
    Returns the MongoDB database instance. Connects if not already connected.
    """
    if db is None:
        return connect_to_mongodb()
    return db

def close_mongodb_connection():
    """
    Closes the MongoDB connection.
    """
    global client, db
    if client is not None:
        client.close()
        print("MongoDB connection closed.")
        client = None
        db = None

# Example usage (for testing, will be called from app.py)
if __name__ == "__main__":
    try:
        database = get_db()
        print("Collections in database:", database.list_collection_names())
    except Exception as e:
        print(f"Failed to connect and get collections: {e}")
    finally:
        close_mongodb_connection()
