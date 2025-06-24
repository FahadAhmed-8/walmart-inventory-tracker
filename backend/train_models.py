# backend/train_models.py
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression # Model 1
from sklearn.ensemble import RandomForestRegressor # Model 2
import lightgbm as lgb # Model 3
from sklearn.metrics import mean_absolute_error, r2_score
import joblib # For saving/loading models and preprocessors
import os
import datetime

# --- Configuration ---
DATASET_PATH = 'retail_inventory_forecast.csv'
MODELS_DIR = 'ml_models' # Directory to save trained models
TARGET_VARIABLE = 'Units Sold' # What we want to predict

# Ensure models directory exists
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

# --- 1. Data Loading and Initial Preprocessing ---
def load_and_preprocess_data(file_path):
    """Loads CSV, cleans column names, converts Date, handles missing values."""
    print(f"Loading data from {file_path}...")
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip() # Clean column names
    
    # Convert 'Date' to datetime objects
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Handle missing values (simple imputation for numerical, fill with 'Unknown' for categorical)
    for col in ['Inventory Level', 'Units Sold', 'Units Ordered', 'Price', 'Discount', 'Competitor Pricing']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].mean())
    
    # For categorical columns, fillna with a placeholder before encoding
    categorical_cols = ['Store ID', 'Product ID', 'Category', 'Region', 'Weather Condition', 'Holiday/Promotion', 'Seasonality']
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna('Unknown') # Ensure they are strings before encoding

    # Drop 'Demand Forecast' if it's in the original dataset and we are predicting 'Units Sold'
    # This avoids data leakage if "Demand Forecast" itself is derived from future knowledge.
    if 'Demand Forecast' in df.columns:
        df = df.drop(columns=['Demand Forecast'])

    print(f"Data loaded. Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    return df

# --- 2. Feature Engineering ---
def engineer_features(df):
    """Creates time-based and other derived features."""
    print("Engineering features...")
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['DayOfWeek'] = df['Date'].dt.dayofweek # Monday=0, Sunday=6
    df['WeekOfYear'] = df['Date'].dt.isocalendar().week.astype(int) # Week of the year
    
    # Lagged features (requires sorting by Date and then by Store/Product for correct lags)
    df = df.sort_values(by=['Store ID', 'Product ID', 'Date'])
    df['Units Sold Lag1'] = df.groupby(['Store ID', 'Product ID'])['Units Sold'].shift(1).fillna(0) # Previous day's sales
    df['Inventory Level Lag1'] = df.groupby(['Store ID', 'Product ID'])['Inventory Level'].shift(1).fillna(0) # Previous day's inventory

    # Ensure price and discount are numerical (if not already handled)
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(df['Price'].mean())
    df['Discount'] = pd.to_numeric(df['Discount'], errors='coerce').fillna(0) # Discounts often start at 0

    print("Features engineered.")
    return df

# --- 3. Feature Selection and Preprocessing Pipeline ---
def create_preprocessor(df):
    """Creates a preprocessor pipeline for numerical and categorical features."""
    
    # Define features for the model
    numerical_features = [
        'Inventory Level', 'Price', 'Discount', 'Units Sold Lag1', 'Inventory Level Lag1',
        'Units Ordered', # Use Units Ordered if it's available as input feature not target
        'Competitor Pricing'
    ]
    categorical_features = [
        'Store ID', 'Product ID', 'Category', 'Region', 'Weather Condition',
        'Holiday/Promotion', 'Seasonality',
        'Year', 'Month', 'Day', 'DayOfWeek', 'WeekOfYear' # Time features as categorical for encoding
    ]

    # Filter out columns that are not in the DataFrame
    numerical_features = [f for f in numerical_features if f in df.columns]
    categorical_features = [f for f in categorical_features if f in df.columns]

    # Create a column transformer for preprocessing
    # OneHotEncoder for categorical features (handle_unknown='ignore' for unseen categories in prediction)
    # Numerical features are not scaled for tree-based models, but can be for linear models.
    # For simplicity and general compatibility, we'll just pass them through or scale them.
    # For now, let's just pass numerical through.
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numerical_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    print("Preprocessor created.")
    return preprocessor, numerical_features, categorical_features

# --- 4. Model Training and Evaluation ---
def train_and_evaluate_model(model, X_train, y_train, X_test, y_test, model_name):
    """Trains and evaluates a given model."""
    print(f"\n--- Training {model_name} ---")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"{model_name} MAE: {mae:.2f}")
    print(f"{model_name} R-squared: {r2:.2f}")
    return model, mae, r2

# --- Main Training Function ---
def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, DATASET_PATH)

    df = load_and_preprocess_data(csv_file_path)
    df = engineer_features(df)

    # Sort data by date for time-series split
    df = df.sort_values(by='Date')

    # Define features (X) and target (y)
    # Exclude 'Date' and the target variable from features
    features_to_exclude = ['Date', TARGET_VARIABLE]
    X = df.drop(columns=features_to_exclude, errors='ignore')
    y = df[TARGET_VARIABLE]

    # Time-series split: train on earlier data, test on later data
    # Use 80% for training, 20% for testing
    split_point = int(len(df) * 0.8)
    X_train_df, X_test_df = X.iloc[:split_point], X.iloc[split_point:]
    y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]

    # Create preprocessor based on the training data
    preprocessor, numerical_features, categorical_features = create_preprocessor(X_train_df)

    # Apply preprocessing to training and testing data
    X_train_processed = preprocessor.fit_transform(X_train_df)
    X_test_processed = preprocessor.transform(X_test_df)
    print("Data preprocessed for models.")
    print(f"X_train_processed shape: {X_train_processed.shape}")
    print(f"X_test_processed shape: {X_test_processed.shape}")


    # --- Initialize and Train Models ---
    best_model = None
    best_mae = float('inf')
    best_model_name = ""

    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "LightGBM Regressor": lgb.LGBMRegressor(random_state=42, n_jobs=-1)
    }

    for name, model in models.items():
        trained_model, mae, r2 = train_and_evaluate_model(model, X_train_processed, y_train, X_test_processed, y_test, name)
        if mae < best_mae:
            best_mae = mae
            best_model = trained_model
            best_model_name = name

    print(f"\n--- Best Model: {best_model_name} (MAE: {best_mae:.2f}) ---")

    # --- Save the best model and preprocessor ---
    model_filename = os.path.join(current_dir, MODELS_DIR, f'best_demand_forecast_model_{best_model_name.replace(" ", "_").lower()}.joblib')
    preprocessor_filename = os.path.join(current_dir, MODELS_DIR, 'feature_preprocessor.joblib')
    
    joblib.dump(best_model, model_filename)
    joblib.dump(preprocessor, preprocessor_filename)
    joblib.dump(numerical_features, os.path.join(current_dir, MODELS_DIR, 'numerical_features.joblib'))
    joblib.dump(categorical_features, os.path.join(current_dir, MODELS_DIR, 'categorical_features.joblib'))

    print(f"\nBest model saved to: {model_filename}")
    print(f"Preprocessor saved to: {preprocessor_filename}")
    print("Numerical and categorical feature lists saved.")

if __name__ == '__main__':
    main()
