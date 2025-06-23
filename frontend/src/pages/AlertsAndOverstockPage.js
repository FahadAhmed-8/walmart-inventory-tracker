// frontend/src/pages/AlertsAndOverstockPage.js
import React, { useState } from 'react'; // Removed useEffect as it's not directly used for rendering logic anymore
import { getLowStockAlerts, getOverstockedAlerts, downloadCSV } from '../api/inventoryApi';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

// Custom Tooltip for Recharts (Understocked)
const UnderstockTooltip = ({ active, payload, label }) => {
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

// Custom Tooltip for Recharts (Overstocked)
const OverstockTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <p className="label">{`Product: ${data.product_name} (${data.product_id}) @ Store: ${data.store_id}`}</p>
        <p className="intro">{`Current Stock: ${data.current_stock}`}</p>
        <p className="intro">{`Projected Demand (${data.days_for_demand} days): ${data.projected_demand_for_X_days}`}</p>
        <p className="desc">{`Overstock Ratio: ${data.overstock_ratio}x (Threshold: ${data.threshold_multiplier}x)`}</p>
        <p className="alert-reason">{data.alert_reason}</p>
      </div>
    );
  }
  return null;
};


function AlertsAndOverstockPage({ setMessage, setError, clearMessages }) {
  const [storeId, setStoreId] = useState(''); // Unified store ID for filtering both alerts
  const [daysLeftAlert, setDaysLeftAlert] = useState(7); // For understocked
  const [understockedAlerts, setUnderstockedAlerts] = useState([]);

  const [thresholdMultiplier, setThresholdMultiplier] = useState(3.0); // For overstocked
  const [daysForDemand, setDaysForDemand] = useState(30); // For overstocked
  const [overstockedAlerts, setOverstockedAlerts] = useState([]);


  // --- Understocked Alerts Logic ---
  const fetchUnderstockedAlerts = async () => {
    clearMessages();
    try {
      const data = await getLowStockAlerts(daysLeftAlert, storeId);
      setUnderstockedAlerts(data);
      if (data.length === 0) {
        setMessage('No understocked alerts found for the specified criteria.');
      } else {
        setMessage(`Found ${data.length} understocked alerts.`);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch understocked alerts.');
      setUnderstockedAlerts([]);
    }
  };

  const handleExportUnderstockedCSV = () => {
    downloadCSV(understockedAlerts, `understocked_alerts_${storeId || 'all'}_${daysLeftAlert}days.csv`);
    setMessage('Understocked alerts exported to CSV.');
  };

  // --- Overstocked Alerts Logic ---
  const fetchOverstockedAlerts = async () => {
    clearMessages();
    try {
      const data = await getOverstockedAlerts(thresholdMultiplier, daysForDemand, storeId);
      setOverstockedAlerts(data);
      if (data.length === 0) {
        setMessage('No overstocked alerts found for the specified criteria.');
      } else {
        setMessage(`Found ${data.length} overstocked alerts.`);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch overstocked alerts.');
      setOverstockedAlerts([]);
    }
  };

  const handleExportOverstockedCSV = () => {
    downloadCSV(overstockedAlerts, `overstocked_alerts_${storeId || 'all'}_${thresholdMultiplier}x_${daysForDemand}days.csv`);
    setMessage('Overstocked alerts exported to CSV.');
  };

  return (
    <>
      <section className="card">
        <h2>Understocked Products</h2>
        <div className="input-group">
          <label>
            Store ID (Optional Filter):
            <input type="text" value={storeId} onChange={(e) => setStoreId(e.target.value)} placeholder="e.g., S1" />
          </label>
          <label>
            Days Left Threshold:
            <input
              type="number"
              value={daysLeftAlert}
              onChange={(e) => setDaysLeftAlert(parseInt(e.target.value) || 0)}
              placeholder="e.g., 7"
            />
          </label>
          <button onClick={fetchUnderstockedAlerts}>Get Understocked Alerts</button>
          <button onClick={handleExportUnderstockedCSV} disabled={understockedAlerts.length === 0}>Export CSV</button>
        </div>

        {understockedAlerts.length > 0 && (
          <div className="alerts-display">
            <h3>Understocked Products (within {daysLeftAlert} days):</h3>
            
            {/* Recharts Bar Chart for Understocked */}
            <div className="chart-container-recharts">
              <ResponsiveContainer width={Math.max(understockedAlerts.length * 70 + 100, 100)} height={300}> 
                <BarChart data={understockedAlerts} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="product_id" 
                    angle={-45} 
                    textAnchor="end" 
                    interval={0} 
                    height={70} 
                  />
                  <YAxis label={{ value: 'Days Remaining', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<UnderstockTooltip />} />
                  <Legend verticalAlign="top" height={36} />
                  <Bar dataKey="days_remaining" name="Days Remaining" fill="#3498db" />
                  <Bar dataKey="min_replenish_time" name="Min. Replenish Time" fill="#27ae60" opacity={0.7} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            <ul className="alert-list">
              {understockedAlerts.map((alert, index) => (
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
        {understockedAlerts.length === 0 && ( // Removed 'message.includes' check as message is handled centrally
          <p className="no-alerts-message">No understocked alerts found matching criteria.</p>
        )}
      </section>

      <section className="card">
        <h2>Overstocked Products</h2>
        <div className="input-group">
          <label>
            Store ID (Optional Filter):
            <input type="text" value={storeId} onChange={(e) => setStoreId(e.target.value)} placeholder="e.g., S1" />
          </label>
          <label>
            Threshold Multiplier:
            <input
              type="number"
              step="0.1"
              value={thresholdMultiplier}
              onChange={(e) => setThresholdMultiplier(parseFloat(e.target.value) || 0)}
              placeholder="e.g., 3.0"
            />
          </label>
          <label>
            Days for Demand Projection:
            <input
              type="number"
              value={daysForDemand}
              onChange={(e) => setDaysForDemand(parseInt(e.target.value) || 0)}
              placeholder="e.g., 30"
            />
          </label>
          <button onClick={fetchOverstockedAlerts}>Get Overstocked Alerts</button>
          <button onClick={handleExportOverstockedCSV} disabled={overstockedAlerts.length === 0}>Export CSV</button>
        </div>

        {overstockedAlerts.length > 0 && (
          <div className="alerts-display">
            <h3>Overstocked Products (Current Stock > {thresholdMultiplier}x Demand for {daysForDemand} days):</h3>
             {/* Recharts Bar Chart for Overstocked */}
            <div className="chart-container-recharts">
              <ResponsiveContainer width={Math.max(overstockedAlerts.length * 70 + 100, 100)} height={300}>
                <BarChart data={overstockedAlerts} margin={{ top: 20, right: 30, left: 20, bottom: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="product_id"
                    angle={-45}
                    textAnchor="end"
                    interval={0}
                    height={70}
                  />
                  <YAxis label={{ value: 'Overstock Ratio', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<OverstockTooltip />} />
                  <Legend verticalAlign="top" height={36} />
                  <Bar dataKey="overstock_ratio" name="Overstock Ratio" fill="#28a745" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <ul className="alert-list">
              {overstockedAlerts.map((alert, index) => (
                <li key={index} className="alert-item overstocked-alert">
                  <p><strong>Product:</strong> {alert.product_name} ({alert.product_id}) at <strong>Store:</strong> {alert.store_id}</p>
                  <p><strong>Current Stock:</strong> {alert.current_stock} &nbsp; <strong>Daily Demand:</strong> {alert.daily_demand_sim}</p>
                  <p><strong>Projected Demand ({alert.days_for_demand} days):</strong> {alert.projected_demand_for_X_days}</p>
                  <p><strong>Overstock Ratio:</strong> <span className="overstock-ratio-label">{alert.overstock_ratio}x</span> (Threshold: {alert.threshold_multiplier}x)</p>
                  <p className="alert-reason-text">{alert.alert_reason}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
        {overstockedAlerts.length === 0 && ( // Removed 'message.includes' check
          <p className="no-alerts-message">No overstocked alerts found matching criteria.</p>
        )}
      </section>
    </>
  );
}

export default AlertsAndOverstockPage;
