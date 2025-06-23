// frontend/src/App.js
import React, { useState, useEffect } from 'react'; // Removed useRef as Recharts handles refs internally
import './App.css';
import { getInventory, recordSale, recordReceipt, getLowStockAlerts, uploadSalesCSV, uploadReceiptsCSV } from './api/inventoryApi';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'; // Recharts imports

function App() {
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('');
  const [inventoryData, setInventoryData] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [daysLeftAlert, setDaysLeftAlert] = useState(7);
  const [alerts, setAlerts] = useState([]);

  const [selectedSalesFile, setSelectedSalesFile] = useState(null);
  const [selectedReceiptsFile, setSelectedReceiptsFile] = useState(null);

  const clearMessages = () => {
    setMessage('');
    setError('');
  };

  // --- Individual Item Actions ---
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

  const handleSale = async () => {
    clearMessages();
    if (!storeId || !productId || !quantity) {
      setError('Please enter Store ID, Product ID, and Quantity for sale.');
      return;
    }
    try {
      const data = await recordSale(storeId, productId, parseInt(quantity));
      setMessage(`Sale recorded: New stock level for ${data.product_id} at ${data.store_id} is ${data.new_stock_level}.`);
      setQuantity('');
      fetchInventory();
    } catch (err) {
      setError(err.message || 'Failed to record sale.');
    }
  };

  const handleReceipt = async () => {
    clearMessages();
    if (!storeId || !productId || !quantity) {
      setError('Please enter Store ID, Product ID, and Quantity for receipt.');
      return;
    }
    try {
      const data = await recordReceipt(storeId, productId, parseInt(quantity));
      setMessage(`Receipt recorded: New stock level for ${data.product_id} at ${data.store_id} is ${data.new_stock_level}.`);
      setQuantity('');
      fetchInventory();
    } catch (err) {
      setError(err.message || 'Failed to record receipt.');
    }
  };

  // --- Low Stock Alerts ---
  const fetchLowStockAlerts = async () => {
    clearMessages();
    try {
      const data = await getLowStockAlerts(daysLeftAlert, storeId);
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

  // Custom Tooltip for Recharts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload; // Access the full data object for the hovered bar
      return (
        <div className="custom-tooltip">
          <p className="label">{`Product: ${data.product_id} @ Store: ${data.store_id}`}</p>
          <p className="intro">{`Days Remaining: ${data.days_remaining}`}</p>
          <p className="intro">{`Min. Replenish Time: ${data.min_replenish_time}`}</p>
          <p className="desc">{`Current Stock: ${data.current_stock}, Daily Demand: ${data.daily_demand_sim}`}</p>
          <p className="alert-type">{`Alert Type: ${data.alert_category}`}</p>
          <p className="alert-reason">{data.alert_reason}</p>
        </div>
      );
    }
    return null;
  };


  // --- Batch Operations ---
  const handleSalesFileChange = (event) => {
    setSelectedSalesFile(event.target.files[0]);
  };

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
      setSelectedSalesFile(null);
    } catch (err) {
      setError(err.message || 'Failed to upload sales CSV.');
    }
  };

  const handleReceiptsFileChange = (event) => {
    setSelectedReceiptsFile(event.target.files[0]);
  };

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
      setSelectedReceiptsFile(null);
    } catch (err) {
      setError(err.message || 'Failed to upload receipts CSV.');
    }
  };

  return (
    <div className="App">
      <h1>Walmart Inventory Tracker</h1>

      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}

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
          <button onClick={fetchLowStockAlerts}>Get Alerts (for {storeId || 'All Stores'})</button>
        </div>

        {alerts.length > 0 && (
          <div className="alerts-display">
            <h3>Low Stock Alerts (within {daysLeftAlert} days):</h3>
            
            {/* Recharts Bar Chart */}
            <div className="chart-container-recharts">
              {/* Ensure enough width for all bars + spacing, otherwise enable horizontal scroll */}
              <ResponsiveContainer width={Math.max(alerts.length * 70 + 100, 100)} height={300}> 
                <BarChart data={alerts} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="product_id" 
                    angle={-45} 
                    textAnchor="end" 
                    interval={0} 
                    height={70} 
                    // Add tooltips for XAxis labels if they are long
                    // label={{ value: 'Product ID', position: 'insideBottom', offset: -10 }}
                  />
                  <YAxis label={{ value: 'Days Remaining', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<CustomTooltip />} /> {/* Use custom tooltip */}
                  <Legend verticalAlign="top" height={36} />
                  {/* Bar for Days Remaining */}
                  <Bar dataKey="days_remaining" name="Days Remaining" fill="#3498db" />
                  {/* Optional: Line for Min. Replenish Time, can be a second bar or a reference line if data structure allows */}
                  <Bar dataKey="min_replenish_time" name="Min. Replenish Time" fill="#27ae60" opacity={0.7} />

                  {/* Reference lines for thresholds if desired */}
                  {/* <ReferenceLine y={daysLeftAlert} label="Threshold" stroke="#e74c3c" strokeDasharray="3 3" /> */}
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            <ul className="alert-list"> {/* Vertical scrollbar for this list */}
              {alerts.map((alert, index) => (
                <li key={index} className={`alert-item ${alert.alert_category.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
                  <p><strong>Product:</strong> {alert.product_id} at <strong>Store:</strong> {alert.store_id}</p>
                  <p><strong>Current Stock:</strong> {alert.current_stock} &nbsp; <strong>Daily Demand:</strong> {alert.daily_demand_sim}</p>
                  <p><strong>Days Remaining:</strong> <span className="days-remaining">{alert.days_remaining}</span> days</p>
                  <p><strong>Min. Replenish Time:</strong> {alert.min_replenish_time} days</p>
                  <p><strong>Alert Type:</strong> <span className="alert-category-label">{alert.alert_category}</span></p>
                  <p className="alert-reason-text">{alert.alert_reason}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
        {alerts.length === 0 && message.includes('No low stock alerts') && (
          <p className="no-alerts-message">No low stock alerts found matching criteria.</p>
        )}
      </section>

      <section className="card">
        <h2>Bulk Inventory Actions (CSV)</h2>
        <div className="input-group">
          <h3>Upload Sales CSV</h3>
          <input type="file" accept=".csv" onChange={handleSalesFileChange} />
          <button onClick={handleUploadSalesCSV} disabled={!selectedSalesFile}>Upload Sales</button>
          <p className="hint">CSV columns: store_id,product_id,quantity</p>
        </div>
        <div className="input-group">
          <h3>Upload Receipts CSV</h3>
          <input type="file" accept=".csv" onChange={handleReceiptsFileChange} />
          <button onClick={handleUploadReceiptsCSV} disabled={!selectedReceiptsFile}>Upload Receipts</button>
          <p className="hint">CSV columns: store_id,product_id,quantity</p>
        </div>
      </section>
    </div>
  );
}

export default App;
