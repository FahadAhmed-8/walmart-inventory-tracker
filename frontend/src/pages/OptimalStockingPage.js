// frontend/src/pages/OptimalStockingPage.js
import React, { useState } from 'react';
import { getOptimalStocking, getRemediationActions } from '../api/inventoryApi';

function OptimalStockingPage({ setMessage, setError, clearMessages }) {
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [optimalStockingData, setOptimalStockingData] = useState(null);
  const [remediationActions, setRemediationActions] = useState([]);

  // NEW: State for hover card visibility and content
  const [hoveredAction, setHoveredAction] = useState(null);
  const [hoverCardPosition, setHoverCardPosition] = useState({ x: 0, y: 0 });

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
      await handleFetchRemediationActions(storeId, productId);
    } catch (err) {
      setError(err.message || 'Failed to fetch optimal stocking data.');
      setOptimalStockingData(null);
      setRemediationActions([]);
    }
  };

  const handleFetchRemediationActions = async (targetStoreId, targetProductId) => {
    clearMessages();
    try {
      const data = await getRemediationActions(targetStoreId, targetProductId); 
      setRemediationActions(data);
      if (data.length === 0) {
        setMessage(`No intelligent remediation actions found for ${targetProductId} @ ${targetStoreId}.`);
      } else {
        setMessage(`Found ${data.length} intelligent remediation actions for ${targetProductId} @ ${targetStoreId}.`);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch remediation actions.');
      setRemediationActions([]);
    }
  };

  // NEW: Hover event handlers
  const handleMouseEnterAction = (e, action) => {
    setHoveredAction(action);
    // Position the hover card relative to the mouse pointer
    setHoverCardPosition({ x: e.clientX + 15, y: e.clientY + 15 }); // Offset by 15px
  };

  const handleMouseLeaveAction = () => {
    setHoveredAction(null);
  };

  return (
    <section className="page-content">
      <h1>Intelligent Inventory Optimization & Remediation</h1>

      <div className="card">
        <h2>Optimal Stocking & Strategic Actions</h2>
        <p className="hint">
          Enter product and store details to determine the optimal inventory level.
          Based on the stock status, the system will provide strategic actions,
          including intelligent transfer recommendations.
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
          <button onClick={handleGetOptimalStocking}>Analyze Stock & Get Actions</button>
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
            <p>
              <strong>Original Lead Time:</strong> {optimalStockingData.min_replenish_time} days
              {optimalStockingData.current_lead_time_override > 0 && (
                <span> (+{optimalStockingData.current_lead_time_override} days override)</span>
              )}
            </p>
            <p><strong>Effective Lead Time:</strong> {optimalStockingData.effective_lead_time} days</p>
            
            {/* Optimal Stocking Breakdown & Badge */}
            <div className="optimal-stock-summary">
              <h3><span className="highlight-text">Target Inventory Level:</span></h3>
              <div
                className={`stock-badge ${
                  optimalStockingData.target_inventory_level > optimalStockingData.current_stock
                    ? "understock"
                    : optimalStockingData.target_inventory_level < optimalStockingData.current_stock
                      ? "overstock"
                      : ""
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

      {/* Remediation Actions Display Section - NOW INCLUDES TRANSFER */}
      {remediationActions.length > 0 && optimalStockingData && (
        <div className="card remediation-actions-display" style={{ marginTop: '25px' }}>
          <h2>Strategic Remediation Actions</h2>
          <p className="hint">
            Prioritized suggestions to address stock deviations, including inter-store transfers where viable.
            Hover over an action for estimated financial impact.
          </p>
          <ul className="alert-list remediation-list">
            {remediationActions.map((action, index) => (
              <li
                key={index}
                className={`alert-item action-item priority-${action.priority}`}
                onMouseEnter={(e) => handleMouseEnterAction(e, action)}
                onMouseLeave={handleMouseLeaveAction}
              >
                {action.action_type === 'Transfer' ? (
                  <>
                    <p>
                      <strong>Product:</strong> {action.product_id}
                      <br />
                      <strong>From Store:</strong> {action.source_store_id} &nbsp; &nbsp;
                      <strong>To Store:</strong> {action.target_store_id}
                    </p>
                    <p>
                      <strong>Action:</strong>
                      <span className="action-type-label action-transfer">
                        📦 Transfer {action.suggested_quantity} units
                      </span>
                    </p>
                    <p>
                      <strong>Viability:</strong>
                      <div
                        className={`feasibility-badge ${action.transfer_details.viability_category}`}
                        title={`Breakdown:
• Distance Score: ${action.transfer_details.distance_score}/100
• Cost Score: ${action.transfer_details.cost_score}/100
• Historical Success Score: ${action.transfer_details.historical_success_score}/100
Weighted Avg: (Dist * 40%) + (Cost * 30%) + (Success * 30%)
Calculated Distance: ${action.transfer_details.calculated_distance_km} km
Estimated Transfer Cost: $${action.transfer_details.calculated_transfer_cost}`}
                      >
                        <span>{action.transfer_details.final_feasibility_score}/100</span>
                      </div>
                    </p>
                  </>
                ) : (
                  <>
                    <p><strong>Product:</strong> {action.product_id} at <strong>Store:</strong> {action.store_id}</p>
                    <p><strong>Current Stock:</strong> {action.current_stock} &nbsp; <strong>Optimal Target:</strong> {action.optimal_target_level}</p>
                    <p>
                      <strong>Action:</strong>
                      <span className={`action-type-label ${action.action_type === 'Order' ? 'action-order' : 'action-promote'}`}>
                        {action.action_type === 'Order' ? '🛒 Order' : '📢 Promote'} {action.suggested_quantity} units
                      </span>
                    </p>
                  </>
                )}
                <p><strong>Priority:</strong> <span className={`priority-label ${action.priority}`}>{action.priority.toUpperCase()}</span></p>
                <p className="alert-reason-text">{action.reason}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* NEW: Hover Card for Action Impact Simulation */}
      {hoveredAction && (
        <div 
          className="action-impact-hover-card" 
          style={{ left: hoverCardPosition.x, top: hoverCardPosition.y }}
        >
          <h4>Estimated Financial Impact:</h4>
          <p><strong>Net Profit:</strong> <span className={hoveredAction.estimated_net_profit >= 0 ? 'profit-positive' : 'profit-negative'}>${hoveredAction.estimated_net_profit.toFixed(2)}</span></p>
          {hoveredAction.associated_cost > 0 && (
            <p><strong>Associated Cost:</strong> ${hoveredAction.associated_cost.toFixed(2)}</p>
          )}
          <p className="impact-notes">{hoveredAction.impact_notes}</p>
        </div>
      )}

      {/* General messages based on optimal stocking / remediation */}
      {optimalStockingData === null && storeId && productId && (
        <p className="no-forecast-message" style={{ marginTop: '20px' }}>Click "Analyze Stock & Get Actions" to see recommendations.</p>
      )}
       {optimalStockingData === null && (!storeId || !productId) && (
        <p className="no-forecast-message" style={{ marginTop: '20px' }}>Please enter Store ID and Product ID above to get optimal stocking data.</p>
      )}
       {/* Message when optimal data exists but no remediation actions found */}
       {optimalStockingData && remediationActions.length === 0 && (
         <p className="no-alerts-message" style={{ marginTop: '20px' }}>No remediation actions needed or found for this product at this store.</p>
       )}
    </section>
  );
}

export default OptimalStockingPage;
