// frontend/src/pages/OptimalStockingPage.js
import React, { useState } from 'react';
import { getOptimalStocking } from '../api/inventoryApi';

function OptimalStockingPage({ setMessage, setError, clearMessages }) {
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [optimalStockingData, setOptimalStockingData] = useState(null);

  const handleGetOptimalStocking = async () => {
    clearMessages();
    if (!storeId || !productId) {
      setError('Please enter both Store ID and Product ID to calculate optimal stocking.');
      return;
    }
    try {
      const data = await getOptimalStocking(storeId, productId);
      setOptimalStockingData(data);
      setMessage('Optimal stocking levels calculated successfully.');
    } catch (err) {
      setError(err.message || 'Failed to fetch optimal stocking data.');
      setOptimalStockingData(null);
    }
  };

  return (
    <section className="page-content">
      <h1>Optimal Stocking & Inventory Targets</h1>

      <div className="card">
        <h2>Calculate Target Inventory</h2>
        <p className="hint">
          Enter product and store details to determine the optimal inventory level based on demand forecast,
          base safety stock, and supplier reliability.
        </p>
        <div className="input-group">
          <label>
            Store ID:
            <input type="text" value={storeId} onChange={(e) => setStoreId(e.target.value)} placeholder="e.g., S1" />
          </label>
          <label>
            Product ID:
            <input type="text" value={productId} onChange={(e) => setProductId(e.target.value)} placeholder="e.g., P1" />
          </label>
          <button onClick={handleGetOptimalStocking}>Get Optimal Stocking</button>
        </div>
      </div>

      {optimalStockingData && (
        <div className="card optimal-stocking-results" style={{ marginTop: '20px' }}>
          <h2>Optimal Stocking Breakdown for {optimalStockingData.product_id} @ {optimalStockingData.store_id}</h2>
          <div className="inventory-display">
            <p><strong>Current Stock:</strong> {optimalStockingData.current_stock} units</p>
            <p><strong>Base Safety Stock:</strong> {optimalStockingData.base_safety_stock} units</p>
            <p><strong>Supplier Reliability:</strong> {optimalStockingData.supplier_category_reliability} (Higher is better)</p>
            <p><strong>Calculated Reliability Factor:</strong> {optimalStockingData.reliability_factor}</p>
            <p><strong>Adjusted Safety Stock:</strong> {optimalStockingData.calculated_safety_stock} units (Factoring in reliability)</p>
            
            {/* NEW: Optimal Stocking Breakdown & Badge */}
            <div className="optimal-stock-summary">
              <h3><span className="highlight-text">Target Inventory Level:</span></h3>
              <div
                className={`stock-badge ${
                  optimalStockingData.target_inventory_level > optimalStockingData.current_stock
                    ? "understock" // Target is higher than current, so currently understocked
                    : optimalStockingData.target_inventory_level < optimalStockingData.current_stock
                      ? "overstock" // Target is lower than current, so currently overstocked
                      : "" // Optimal == current
                }`}
                title={`Breakdown:
• Forecast (30-day): ${optimalStockingData.total_30_day_forecasted_demand} units
• Safety Stock (Adjusted): ${optimalStockingData.calculated_safety_stock} units
Current Stock: ${optimalStockingData.current_stock} units
Recommended Action: ${
  optimalStockingData.target_inventory_level > optimalStockingData.current_stock
    ? `Increase stock by ${optimalStockingData.target_inventory_level - optimalStockingData.current_stock} units`
    : optimalStockingData.target_inventory_level < optimalStockingData.current_stock
      ? `Reduce stock by ${optimalStockingData.current_stock - optimalStockingData.target_inventory_level} units`
      : `Stock is currently optimal.`
}`}
              >
                <span>Optimal Target: {optimalStockingData.target_inventory_level} units</span>
              </div>
            </div>

            <p className="hint" style={{ marginTop: '10px' }}>{optimalStockingData.optimal_stocking_notes}</p>
          </div>
        </div>
      )}

      {optimalStockingData === null && storeId && productId && (
        <p className="no-forecast-message" style={{ marginTop: '20px' }}>Click "Get Optimal Stocking" to see recommendations.</p>
      )}
       {optimalStockingData === null && (!storeId || !productId) && (
        <p className="no-forecast-message" style={{ marginTop: '20px' }}>Please enter Store ID and Product ID above to get optimal stocking data.</p>
      )}
    </section>
  );
}

export default OptimalStockingPage;
