Walmart Inventory Management App
Welcome to the Walmart Inventory Management App! This project provides a robust solution for managing store inventory, tracking transactions, generating crucial alerts, and leveraging machine learning for accurate demand forecasting and smart reorder recommendations. Designed with scalability and ease of use in mind, it aims to optimize stock levels, prevent shortages, and reduce overstocking.
1. About the Product
The Walmart Inventory Management App is a full-stack application built to empower store managers and inventory planners with real-time insights and predictive capabilities. It addresses common inventory challenges by offering a suite of features:
Key Features:
Real-time Inventory Tracking: View current stock levels for any product at any store.
Transaction Recording: Easily record sales and new stock receipts, either individually or in batches via CSV uploads.
Low Stock Alerts: Proactively identify products at risk of running out, considering their average daily sales and replenishment lead times. Critical alerts are highlighted for immediate action.
Overstocked Alerts: Pinpoint products that are excessively stocked, helping to prevent wastage and optimize warehouse space.
AI-Powered Demand Forecasting: Generate daily demand predictions for specific product-store combinations using a trained Machine Learning model. This includes:
"What-If" Scenario Analysis: Dynamically adjust factors like future discounts, holidays, weather conditions, product prices, and competitor pricing to see their potential impact on demand.
Smart Reorder Recommendations: Receive data-driven suggestions on when and how much to reorder, calculated based on forecasted demand, product lead times, safety stock levels, and current inventory.
Data Export: Export demand forecasts to CSV for further analysis or reporting.
How it Helps:
This application helps Walmart stores and distribution centers to:
Reduce Stockouts: By predicting demand and alerting on low stock, ensuring popular items are always available.
Minimize Overstocking: Identifying surplus inventory reduces carrying costs and potential waste.
Improve Operational Efficiency: Automating alerts and recommendations frees up time for strategic planning.
Enhance Decision Making: Data-driven insights enable smarter purchasing and pricing strategies.
2. Repository Overview
This repository contains the complete codebase for the Walmart Inventory Management App, including both the backend API and the frontend user interface.
Tech Stack Used:
Backend: Python (Flask, Pandas, Scikit-learn, PyMongo)
Frontend: React.js
Database: MongoDB
Machine Learning: XGBoost Regressor for demand forecasting.
File and Directory Structure:
Here's a summary of the key files and directories:
walmart_inventory_app/
├── backend/
│   ├── app.py
│   ├── db_client.py
│   ├── ml_models/
│   │   ├── best_demand_forecast_model_*.joblib
│   │   ├── categorical_features.joblib
│   │   ├── numerical_features.joblib
│   │   └── feature_preprocessor.joblib
│   └── services/
│       └── inventory_service.py
├── frontend/
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── api/
│       │   └── inventoryApi.js
│       ├── components/
│       │   └── (e.g., LineChart.js, etc.)
│       ├── pages/
│       │   ├── DemandForecastPage.js
│       │   ├── InventoryAlertsPage.js
│       │   ├── InventoryPage.js
│       │   └── ...
│       ├── App.js
│       ├── index.css
│       └── index.js
├── data/
│   ├── initial_products.csv
│   ├── initial_stores.csv
│   ├── initial_inventory.csv
│   ├── initial_sales_history.csv
│   ├── products.json (generated)
│   ├── stores.json (generated)
│   └── inventory.json (generated)
├── data_prep.py
├── model_training.py
├── requirements.txt
└── README.md


File Summaries and Their Use:
backend/app.py:
This is the main Flask application entry point.
It defines all the API endpoints (/inventory, /inventory/sale, /inventory/forecast, etc.) that the frontend interacts with.
It handles request parsing, calls appropriate service functions, and returns JSON responses.
Crucially, it loads the trained ML model and preprocessor into memory when the Flask app starts, making them available for real-time predictions.
backend/db_client.py:
Manages the MongoDB connection.
Contains functions to establish and retrieve the database client instance.
backend/ml_models/:
This directory stores the pre-trained machine learning artifacts.
best_demand_forecast_model_*.joblib: The serialized XGBoost Regressor model.
feature_preprocessor.joblib: The ColumnTransformer used to preprocess features before feeding them to the model.
numerical_features.joblib, categorical_features.joblib: Lists of feature names used during model training, ensuring consistency during prediction.
backend/services/inventory_service.py:
This file contains the core business logic of the application.
It interacts directly with the MongoDB database (via db_client.py) to perform operations like fetching inventory, recording transactions, and retrieving alert data.
It houses the logic for ML model inference (calling the loaded model to get forecasts) and the reorder recommendation algorithm.
It also includes functions for initial data loading and CSV batch processing.
frontend/src/api/inventoryApi.js:
Acts as the communication layer between the React frontend and the Flask backend.
It contains asynchronous functions (fetch, axios equivalent) for making HTTP requests to all defined API endpoints.
frontend/src/components/:
Contains reusable React components (e.g., chart components, input fields, buttons) that are used across different pages.
frontend/src/pages/:
Each file here represents a distinct page or view of the application (e.g., Inventory, Alerts, Demand Forecast).
These pages orchestrate fetching data from inventoryApi.js and displaying it using components.
DemandForecastPage.js: Specifically handles user inputs for forecasting, displays the forecast chart, daily details, and integrates the "What-If" scenario analysis and reorder recommendations.
data/:
Contains initial .csv files used to generate the base data for the MongoDB database.
It will also store the .json (NDJSON) files that are created by data_prep.py before being loaded into MongoDB.
data_prep.py:
A utility script responsible for generating synthetic initial data (products, stores, inventory) and converting it into a format suitable for MongoDB import (NDJSON). This is crucial for setting up your development environment.
model_training.py:
This script is used to train the Machine Learning model for demand forecasting.
It loads historical sales data, performs feature engineering, trains an XGBoost Regressor, and then saves the trained model, preprocessor, and feature lists to the ml_models directory.
requirements.txt:
Lists all the Python dependencies required for the backend. Use pip install -r requirements.txt to install them.
package.json:
Lists all the Node.js dependencies required for the frontend. Use npm install to install them.
3. The Demand Prediction Method
The core of the intelligent inventory management lies in its Machine Learning-driven demand forecasting.
What it Predicts:
The model predicts the daily demand (units sold) for a specific product at a specific store for a future number of days.
How it Predicts (The ML Pipeline):
Data Collection/Preparation (data_prep.py): Synthetic historical data resembling sales, inventory, product, and store information is generated.
Feature Engineering (model_training.py): From this raw data, relevant features are extracted that are believed to influence demand. These include:
Temporal Features: Year, Month, Day, Day of Week, Week of Year, Seasonality (Spring, Summer, Autumn, Winter).
Product Attributes: Product Category, Price, Discount.
Store Attributes: Store Region.
Inventory & Sales Lags: Previous day's units sold, previous day's inventory level.
External Factors: Weather Condition, Holiday/Promotion status, Competitor Pricing.
Model Training (model_training.py): An XGBoost Regressor is trained on this prepared historical data. XGBoost is chosen for its robustness, ability to handle various feature types, and high performance in many tabular data prediction tasks. The model learns the complex relationships between the features and the historical daily demand.
Model Persistence: The trained XGBoost model, along with a ColumnTransformer (used for preprocessing new data consistently), and lists of numerical/categorical features are saved (.joblib files) to the backend/ml_models/ directory.
Real-time Prediction (backend/app.py, backend/services/inventory_service.py):
When a user requests a forecast from the frontend, the app.py endpoint calls get_demand_forecast_data_ml in inventory_service.py.
This function constructs a "future" data point for each day being forecasted, using current inventory, product/store details, and any specified "what-if" parameters.
This future data is then transformed using the same preprocessor that was used during training.
Finally, the preprocessed data is fed into the loaded XGBoost model, which outputs the predicted demand for that specific day.
Key Factors Influencing Prediction (Features):
The model considers various factors to make its predictions. These are also the factors you can manipulate in the "What-If" scenario analysis:
Product-Specific:
Product ID: Unique identifier for the product.
Category: Product category (e.g., Electronics, Food, Apparel).
Price: The selling price of the product.
Discount: Any discount applied to the product.
Store-Specific:
Store ID: Unique identifier for the store.
Region: The geographical region of the store.
Temporal/Seasonal:
Date: The specific day for which demand is being predicted.
Year, Month, Day, DayOfWeek, WeekOfYear: Components of the date.
Seasonality: Categorical representation of the season (Spring, Summer, Autumn, Winter).
Inventory & Past Performance:
Inventory Level: The current or last known inventory level.
Units Sold Lag1: The number of units sold on the previous day (a proxy for recent demand).
Inventory Level Lag1: The inventory level from the previous day.
External & Promotional (Adjustable in "What-If"):
Weather Condition: Simulated weather (e.g., Clear, Rainy, Snowy).
Holiday/Promotion: Indicates if a special event or promotion is active (e.g., Holiday Sale, Festival Promotion).
Competitor Pricing: The hypothetical price offered by competitors.
Reorder Recommendations:
The reorder recommendation system builds on top of the demand forecast:
Forecast for Lead Time + Safety Stock: It first forecasts demand for a period covering the product's minimum replenishment lead time plus an additional buffer for safety stock (e.g., 7 days).
Safety Stock Calculation: Determines a safety stock level based on the average daily forecasted demand to mitigate against unexpected demand surges or supply delays.
Reorder Point: Calculates the inventory level at which an order should be placed, considering demand during lead time and safety stock.
Suggested Order Quantity: Recommends the quantity to order to bring the stock level up to a desired target (e.g., 30 days of forecasted demand) plus the safety stock, after the new delivery.
Order & Delivery Dates: Provides suggested dates for placing the order and expected delivery, based on the replenishment lead time.
This holistic approach ensures that reorder decisions are not just reactive but are intelligently informed by future demand projections.
4. Getting Started (For New Contributors)
This section will guide any new person through setting up the project, running it, and understanding how to make changes.
Prerequisites
Before you begin, ensure you have the following installed:
Python 3.8+: Download Python
Node.js (LTS recommended): Download Node.js
MongoDB Community Server: Install MongoDB
Ensure MongoDB is running (e.g., mongod command or as a service).
Setup Instructions
Clone the Repository:
git clone https://github.com/your-username/walmart_inventory_app.git
cd walmart_inventory_app

(Replace https://github.com/your-username/walmart_inventory_app.git with the actual repository URL if different.)
Backend Setup:
Navigate into the backend directory:
cd backend


Create a Python virtual environment:
python -m venv venv


Activate the virtual environment:
On Windows:
.\venv\Scripts\activate


On macOS/Linux:
source venv/bin/activate


Install backend dependencies:
pip install -r requirements.txt


Frontend Setup:
Navigate into the frontend directory:
cd ../frontend


Install frontend dependencies:
npm install


Prepare Initial Data and Train ML Model:
Go back to the project root directory:
cd ..


Run data preparation script: This will create initial product, store, and inventory JSON files in the data/ directory.
python data_prep.py


Train the Machine Learning Model: This will train the demand forecasting model and save its artifacts (.joblib files) in backend/ml_models/. This step is crucial for the forecasting and reorder recommendation features to work.
python model_training.py


Load Initial Data into MongoDB:
Start your Flask backend server (from the backend directory, after activating its venv):
cd backend
flask run


When the Flask app starts, it will automatically attempt to connect to MongoDB and load the initial data from the JSON files generated by data_prep.py. Look for "Starting initial data load from NDJSON files into MongoDB..." in your backend terminal.
Running the Application
Start the Backend Server:
If not already running, from the backend directory (with venv activated):
flask run


The backend will run on http://localhost:5000.
Start the Frontend Development Server:
From a new terminal, navigate to the frontend directory:
cd frontend


Start the React app:
npm start


This will open the application in your browser at http://localhost:3000.
Making Changes:
Backend Logic:
Modify backend/services/inventory_service.py for changes to business rules, database interactions, or ML inference logic.
Modify backend/app.py to add new API endpoints or adjust existing ones.
If you change the ML model or its features, remember to re-run python model_training.py to update the saved model artifacts.
Frontend UI/UX:
Modify files in frontend/src/pages/ for page-specific layouts and logic.
Modify files in frontend/src/components/ to create or update reusable UI elements.
Adjust frontend/src/index.css or create new .css files for styling.
Database Schema:
While MongoDB is schema-less, changes to data structure often require corresponding updates in backend/services/inventory_service.py for data handling.
For testing with new initial data, modify data_prep.py and then run python data_prep.py and restart the backend to reload the data.
Remember to restart the respective server (backend or frontend) after making changes to see them reflected in the application.
