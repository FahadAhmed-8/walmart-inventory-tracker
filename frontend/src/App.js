    // frontend/src/App.js
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
    