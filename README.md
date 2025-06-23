Walmart Real-time Inventory TrackerThis project develops a proof-of-concept for a real-time inventory tracking system, enabling Walmart to monitor product stock levels, record sales and receipts, and generate low-stock alerts. The application is built with a decoupled architecture, featuring a Python Flask backend and a React frontend, backed by MongoDB Atlas for data persistence.Features ImplementedReal-time Stock Inquiry: Retrieve current inventory levels for specific products at any store.Sale Recording: Decrement stock levels atomically upon product sales. Includes checks for insufficient stock.Receipt Recording: Increment stock levels upon receiving new inventory. Supports creating new inventory entries if a product/store combination doesn't exist.Low Stock Alerts: Identify products projected to run out within a defined number of days, based on simulated daily demand. Supports filtering by store.Batch Operations (CSV Upload): Efficiently process multiple sales or receipts by uploading a CSV file.Technologies UsedBackend:Python 3.xFlask: Web framework for building REST APIs.pymongo: Official MongoDB driver for Python.python-dotenv: For loading environment variables.pandas: For CSV processing in batch operations.Flask-CORS: To enable Cross-Origin Resource Sharing for frontend communication.Database:MongoDB Atlas (M0 Sandbox Free Tier): Cloud-hosted NoSQL document database for scalable and flexible data storage.Frontend:React: JavaScript library for building user interfaces.create-react-app: Toolchain for setting up a new React project.JavaScript (or TypeScript if you chose that template).Basic CSS for styling.Version Control: Git & GitHubProject Structure/walmart_inventory_app
├── backend/
│   ├── .env                       # Environment variables (MongoDB URI, etc.)
│   ├── app.py                     # Main Flask application, defines routes
│   ├── db_client.py               # Handles MongoDB connection and common DB operations
│   ├── data_prep.py               # Script to generate initial data JSONs from CSV
│   └── requirements.txt           # Python dependencies
│   # NOTE: retail_inventory_forecast.csv, products.json, stores.json, inventory.json are
│   # ignored by .gitignore as they are source data or generated files.
│
├── frontend/
│   ├── public/                    # Static assets (index.html, favicon)
│   ├── src/                       # React source code
│   │   ├── App.js                 # Main React component, UI logic
│   │   ├── index.js               # React entry point
│   │   ├── api/                   # Functions for interacting with backend API
│   │   │   └── inventoryApi.js
│   │   └── App.css                # Basic styling for the UI
│   ├── .env                       # Environment variables for frontend (Backend API URL)
│   └── package.json               # Frontend dependencies
│
├── .gitignore                     # Specifies files/folders to ignore in Git
└── README.md                      # Project documentation (this file)
Setup and Running the ApplicationFollow these steps to get the application running on your local machine.PrerequisitesPython 3.8+Node.js and npm (or yarn)GitA MongoDB Atlas Account (Free M0 Sandbox cluster is sufficient)The retail_inventory_forecast.csv dataset from Kaggle.1. Backend Setupa. Clone the Repository (if starting fresh)If you're setting this up on a new machine, first clone this repository:git clone <your-repo-url>
cd walmart_inventory_app
b. Prepare Data FilesDownload retail_inventory_forecast.csv from the Kaggle link provided in "Prerequisites".Place the downloaded CSV file into the backend/ directory.Navigate into the backend/ directory:cd backend
(Optional but recommended) Create a Python virtual environment:python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install Python dependencies:pip install -r requirements.txt
# If requirements.txt doesn't exist, first run:
# pip install Flask pymongo python-dotenv pandas Flask-Cors
# Then:
# pip freeze > requirements.txt
Generate the NDJSON files required for database import. Ensure retail_inventory_forecast.csv is in the backend/ directory.python data_prep.py
This will create products.json, stores.json, and inventory.json in your backend/ directory.c. Configure MongoDB Atlas ConnectionCreate a MongoDB Atlas M0 Sandbox Cluster:Go to cloud.mongodb.com and sign up/log in.Create a new project and then "Build a Database" (choose "Shared"/M0 Sandbox).Select your preferred cloud provider and a region close to you.Crucially: Create a Database User with a strong username and password (e.g., walmart_user). Note this password down. Grant Read and write to any database privileges for simplicity.Configure Network Access: Add your current IP address to the IP Access List.Get Your Connection String:From your Atlas cluster overview, click "Connect".Choose "Connect your application".Select "Python" as the driver and "4.0 or later" as the version.Copy the provided connection string.IMPORTANT: Replace <username> and <password> in the copied string with your actual database user credentials.Create .env file for Backend:In the backend/ directory, create a file named .env.Add your filled-in MongoDB URI and a database name:# backend/.env
MONGO_URI="mongodb+srv://your_username:your_password@yourcluster.abcde.mongodb.net/?retryWrites=true&w=majority"
MONGO_DB_NAME="walmart_inventory_db"
Ensure the project's root .gitignore file includes backend/.env.d. Initial Data Load into MongoDB AtlasOpen backend/app.py.Locate the if __name__ == '__main__': block at the very bottom.Ensure load_initial_inventory_data() is UNCOMMENTED and app.run(...) is COMMENTED OUT:if __name__ == '__main__':
    load_initial_inventory_data() # UNCOMMENT THIS
    # app.run(debug=True, host='0.0.0.0', port=5000) # COMMENT THIS OUT
Save app.py.Run the script from your backend/ directory (with venv activated):python app.py
This process will take a long time due to deliberate delays to avoid MongoDB Atlas free tier write limits. Wait for it to complete.e. Run the Flask Backend APIOpen backend/app.py again.Locate the if __name__ == '__main__': block at the very bottom.Ensure load_initial_inventory_data() is COMMENTED OUT and app.run(...) is UNCOMMENTED:if __name__ == '__main__':
    # load_initial_inventory_data() # COMMENT THIS OUT
    try:
        connect_to_mongodb()
    except Exception as e:
        print(f"Application startup aborted due to MongoDB connection error: {e}")
        exit(1)
    app.run(debug=True, host='0.0.0.0', port=5000) # UNCOMMENT THIS
Save app.py.Run the Flask development server from your backend/ directory (with venv activated):flask run
Keep this terminal window open; your backend will be running at http://127.0.0.1:5000.2. Frontend Setupa. Create React ApplicationOpen a new terminal window.Navigate to the walmart_inventory_app/ root directory:cd C:\Users\ASUS\OneDrive\Desktop\walmart_inventory_app
Create the React app:npx create-react-app frontend --template typescript # or omit --template typescript for plain JS
Navigate into the frontend/ directory:cd frontend
b. Configure Frontend EnvironmentIn the frontend/ directory, create a file named .env.Add the backend API URL:# frontend/.env
REACT_APP_BACKEND_URL=http://localhost:5000
Ensure the project's root .gitignore file includes frontend/.env.c. Create API Client ModuleCreate a new folder: frontend/src/apimkdir src\api
Create a file frontend/src/api/inventoryApi.js and paste the following code:// frontend/src/api/inventoryApi.js
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

export const getInventory = async (storeId, productId) => {
    try {
        const response = await fetch(`${BACKEND_URL}/inventory/${storeId}/${productId}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || errorData.error || 'Failed to fetch inventory');
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching inventory:", error);
        throw error;
    }
};

export const recordSale = async (storeId, productId, quantity) => {
    try {
        const response = await fetch(`${BACKEND_URL}/inventory/sale`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ store_id: storeId, product_id: productId, quantity }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to record sale');
        }
        return await response.json();
    } catch (error) {
        console.error("Error recording sale:", error);
        throw error;
    }
};

export const recordReceipt = async (storeId, productId, quantity) => {
    try {
        const response = await fetch(`${BACKEND_URL}/inventory/receipt`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ store_id: storeId, product_id: productId, quantity }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to record receipt');
        }
        return await response.json();
    } catch (error) {
        console.error("Error recording receipt:", error);
        throw error;
    }
};

export const getLowStockAlerts = async (daysLeft, storeId = '') => {
    let url = `${BACKEND_URL}/inventory/low_stock_alerts?days_left=${daysLeft}`;
    if (storeId) {
        url += `&store_id=${storeId}`;
    }
    try {
        const response = await fetch(url);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch low stock alerts');
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching low stock alerts:", error);
        throw error;
    }
};

export const uploadSalesCSV = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await fetch(`${BACKEND_URL}/inventory/sale_batch`, {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to upload sales CSV');
        }
        return await response.json();
    } catch (error) {
        console.error("Error uploading sales CSV:", error);
        throw error;
    }
};

export const uploadReceiptsCSV = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await fetch(`${BACKEND_URL}/inventory/receipt_batch`, {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to upload receipts CSV');
        }
        return await response.json();
    } catch (error) {
        console.error("Error uploading receipts CSV:", error);
        throw error;
    }
};
d. Update Main React Component (App.js) and Styling (App.css)Open frontend/src/App.js and replace its entire content with this code:// frontend/src/App.js
import React, { useState } from 'react';
import './App.css'; // You can customize this CSS or add Tailwind
import { getInventory, recordSale, recordReceipt, getLowStockAlerts, uploadSalesCSV, uploadReceiptsCSV } from './api/inventoryApi';

function App() {
  // State variables to hold form inputs and display data/messages
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('');
  const [inventoryData, setInventoryData] = useState(null); // To display single inventory item
  const [message, setMessage] = useState(''); // For success messages
  const [error, setError] = useState('');     // For error messages
  const [daysLeftAlert, setDaysLeftAlert] = useState(7); // Threshold for low stock alerts
  const [alerts, setAlerts] = useState([]); // To display low stock alerts
  const [selectedSalesFile, setSelectedSalesFile] = useState(null); // For sales CSV upload
  const [selectedReceiptsFile, setSelectedReceiptsFile] = useState(null); // For receipts CSV upload

  // Helper function to clear previous messages
  const clearMessages = () => {
    setMessage('');
    setError('');
  };

  // --- Individual Item Actions ---

  // Fetches and displays inventory for a specific store/product
  const fetchInventory = async () => {
    clearMessages();
    if (!storeId || !productId) {
      setError('Please enter both Store ID and Product ID.');
      return;
    }
    try {
      const data = await getInventory(storeId, productId);
      setInventoryData(data);
      setMessage(`Inventory for ${productId} at ${storeId}: ${data.current_stock} units.`);
    } catch (err) {
      setError(err.message || 'Failed to fetch inventory.');
      setInventoryData(null);
    }
  };

  // Handles recording a sale
  const handleSale = async () => {
    clearMessages();
    if (!storeId || !productId || !quantity) {
      setError('Please enter Store ID, Product ID, and Quantity for sale.');
      return;
    }
    try {
      const data = await recordSale(storeId, productId, parseInt(quantity));
      setMessage(`Sale recorded: New stock level for ${data.product_id} at ${data.store_id} is ${data.new_stock_level}.`);
      setQuantity(''); // Clear quantity input
      fetchInventory(); // Refresh inventory data after sale
    } catch (err) {
      setError(err.message || 'Failed to record sale.');
    }
  };

  // Handles recording a receipt
  const handleReceipt = async () => {
    clearMessages();
    if (!storeId || !productId || !quantity) {
      setError('Please enter Store ID, Product ID, and Quantity for receipt.');
      return;
    }
    try {
      const data = await recordReceipt(storeId, productId, parseInt(quantity));
      setMessage(`Receipt recorded: New stock level for ${data.product_id} at ${data.store_id} is ${data.new_stock_level}.`);
      setQuantity(''); // Clear quantity input
      fetchInventory(); // Refresh inventory data after receipt
    } catch (err) {
      setError(err.message || 'Failed to record receipt.');
    }
  };

  // --- Low Stock Alerts ---

  // Fetches and displays low stock alerts
  const fetchLowStockAlerts = async () => {
    clearMessages();
    try {
      const data = await getLowStockAlerts(daysLeftAlert, storeId); // storeId from state is optional filter
      setAlerts(data);
      if (data.length === 0) {
        setMessage('No low stock alerts found for the specified criteria.');
      } else {
        setMessage(`Found ${data.length} low stock alerts.`);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch low stock alerts.');
      setAlerts([]);
    }
  };

  // --- Batch Operations ---

  // Handles file selection for sales CSV
  const handleSalesFileChange = (event) => {
    setSelectedSalesFile(event.target.files[0]);
  };

  // Handles uploading sales CSV
  const handleUploadSalesCSV = async () => {
    clearMessages();
    if (!selectedSalesFile) {
      setError('Please select a CSV file for sales.');
      return;
    }
    try {
      const result = await uploadSalesCSV(selectedSalesFile);
      setMessage('Sales CSV uploaded and processed. Check console for detailed results (F12).');
      console.log('Batch Sales Result:', result);
      setSelectedSalesFile(null); // Clear selected file input
      // Optionally, refresh inventory display or alerts if relevant
    } catch (err) {
      setError(err.message || 'Failed to upload sales CSV.');
    }
  };

  // Handles file selection for receipts CSV
  const handleReceiptsFileChange = (event) => {
    setSelectedReceiptsFile(event.target.files[0]);
  };

  // Handles uploading receipts CSV
  const handleUploadReceiptsCSV = async () => {
    clearMessages();
    if (!selectedReceiptsFile) {
      setError('Please select a CSV file for receipts.');
      return;
    }
    try {
      const result = await uploadReceiptsCSV(selectedReceiptsFile);
      setMessage('Receipts CSV uploaded and processed. Check console for detailed results (F12).');
      console.log('Batch Receipts Result:', result);
      setSelectedReceiptsFile(null); // Clear selected file input
      // Optionally, refresh inventory display or alerts if relevant
    } catch (err) {
      setError(err.message || 'Failed to upload receipts CSV.');
    }
  };

  return (
    <div className="App">
      <h1>Walmart Inventory Tracker</h1>

      {/* Message and Error Display */}
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}

      {/* Section for Individual Item Actions (Get, Sale, Receipt) */}
      <section className="card">
        <h2>Individual Item Actions</h2>
        <div className="input-group">
          <label>
            Store ID:
            <input type="text" value={storeId} onChange={(e) => setStoreId(e.target.value)} placeholder="e.g., S1" />
          </label>
          <label>
            Product ID:
            <input type="text" value={productId} onChange={(e) => setProductId(e.target.value)} placeholder="e.g., P1" />
          </label>
          <label>
            Quantity (for Sale/Receipt):
            <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="e.g., 10" />
          </label>
        </div>
        <div className="buttons">
          <button onClick={fetchInventory}>Get Inventory</button>
          <button onClick={handleSale}>Record Sale</button>
          <button onClick={handleReceipt}>Record Receipt</button>
        </div>
        {inventoryData && (
          <div className="inventory-display">
            <h3>Current Inventory:</h3>
            <p><strong>Store:</strong> {inventoryData.store_id}</p>
            <p><strong>Product:</strong> {inventoryData.product_id}</p>
            <p><strong>Stock Level:</strong> {inventoryData.current_stock}</p>
            <p><strong>Last Updated:</strong> {inventoryData.last_updated}</p>
          </div>
        )}
      </section>

      {/* Section for Low Stock Alerts */}
      <section className="card">
        <h2>Low Stock Alerts</h2>
        <div className="input-group">
          <label>
            Days Left Threshold:
            <input
              type="number"
              value={daysLeftAlert}
              onChange={(e) => setDaysLeftAlert(parseInt(e.target.value) || 0)}
              placeholder="e.g., 7"
            />
          </label>
          {/* Optional: Filter alerts by the same Store ID input */}
          <button onClick={fetchLowStockAlerts}>Get Alerts (for {storeId || 'All Stores'})</button>
        </div>
        {alerts.length > 0 && (
          <div className="alerts-display">
            <h3>Low Stock Alerts (within {daysLeftAlert} days):</h3>
            <ul className="alert-list">
              {alerts.map((alert, index) => (
                <li key={index}>
                  <strong>Store:</strong> {alert.store_id}, <strong>Product:</strong> {alert.product_id}, <br/>
                  <strong>Stock:</strong> {alert.current_stock}, <strong>Daily Demand:</strong> {alert.daily_demand_sim}, <br/>
                  <strong>Days Remaining:</strong> {alert.days_remaining} ({alert.alert_reason})
                </li>
              ))}
            </ul>
          </div>
        )}
        {alerts.length === 0 && message.includes('No low stock alerts') && (
          <p className="no-alerts-message">No low stock alerts found matching criteria.</p>
        )}
      </section>

      {/* Section for Batch Operations (CSV Upload) */}
      <section className="card">
        <h2>Batch Operations (CSV Upload)</h2>
        <div className="input-group">
          <h3>Upload Sales CSV</h3>
          <input type="file" accept=".csv" onChange={handleSalesFileChange} />
          <button onClick={handleUploadSalesCSV} disabled={!selectedSalesFile}>Upload Sales</button>
          <p className="hint">CSV columns: store_id, product_id, quantity</p>
        </div>
        <div className="input-group">
          <h3>Upload Receipts CSV</h3>
          <input type="file" accept=".csv" onChange={handleReceiptsFileChange} />
          <button onClick={handleUploadReceiptsCSV} disabled={!selectedReceiptsFile}>Upload Receipts</button>
          <p className="hint">CSV columns: store_id, product_id, quantity</p>
        </div>
      </section>
    </div>
  );
}

export default App;
Open frontend/src/App.css and replace its entire content with this CSS:/* frontend/src/App.css */

body {
  font-family: 'Inter', sans-serif; /* Using Inter font as per guidelines */
  background-color: #f0f2f5;
  margin: 0;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start; /* Align items to the start of the cross axis */
  min-height: 100vh;
  color: #333;
}

.App {
  background-color: #ffffff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  max-width: 900px;
  width: 100%;
  box-sizing: border-box;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
}

h2 {
  color: #34495e;
  border-bottom: 2px solid #ecf0f1;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

h3 {
  color: #555;
  margin-top: 15px;
  margin-bottom: 10px;
}

section.card {
  background-color: #fdfdfd;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.input-group {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  align-items: center;
}

.input-group label {
  flex: 1 1 200px; /* Allows labels to grow/shrink but maintain min width */
  display: flex;
  flex-direction: column;
  font-weight: bold;
  color: #4a4a4a;
}

.input-group input[type="text"],
.input-group input[type="number"],
.input-group input[type="file"] {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 16px;
  margin-top: 5px;
  width: 100%; /* Full width within its label container */
  box-sizing: border-box; /* Include padding and border in the element's total width and height */
}

.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 15px;
}

button {
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 20px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

button:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
  box-shadow: none;
}

.message {
  padding: 12px;
  margin-bottom: 20px;
  border-radius: 8px;
  font-weight: bold;
  text-align: center;
}

.message.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.inventory-display, .alerts-display {
  background-color: #ecf0f1;
  padding: 15px;
  border-radius: 8px;
  margin-top: 20px;
  border: 1px dashed #bdc3c7;
}

.inventory-display p {
  margin: 5px 0;
  line-height: 1.5;
}

.alerts-display ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.alerts-display li {
  background-color: #fdfdfd;
  border: 1px solid #ffeeba;
  border-left: 5px solid #ffc107;
  padding: 10px 15px;
  margin-bottom: 10px;
  border-radius: 8px;
  font-size: 0.95em;
}

.no-alerts-message {
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
}

.hint {
  font-size: 0.85em;
  color: #7f8c8d;
  margin-top: 5px;
  width: 100%;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .App {
    padding: 20px;
  }
  .input-group label {
    flex: 1 1 100%; /* Stack inputs on small screens */
  }
  .buttons {
    flex-direction: column; /* Stack buttons on small screens */
  }
  button {
    width: 100%; /* Full width buttons */
  }
}