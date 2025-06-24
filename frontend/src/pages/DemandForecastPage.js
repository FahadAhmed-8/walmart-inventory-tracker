// frontend/src/pages/DemandForecastPage.js
import React, { useState } from 'react';
import { getDemandForecast, getReorderRecommendation, downloadCSV } from '../api/inventoryApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Custom Tooltip for Demand Forecast Chart (simplified back to only predicted demand)
const ForecastTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <p className="label">{`Date: ${data.date}`}</p>
        <p className="intro">{`Predicted Demand: ${data.predicted_demand.toFixed(0)} units`}</p>
        <p className="desc">{`Product ID: ${data.product_id}, Store ID: ${data.store_id}`}</p>
      </div>
    );
  }
  return null;
};

function DemandForecastPage({ setMessage, setError, clearMessages }) {
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [numDays, setNumDays] = useState(30);
  const [forecastData, setForecastData] = useState([]);
  const [reorderRecommendation, setReorderRecommendation] = useState(null);

  // State for Demand Drivers (What-If Scenario inputs)
  const [whatIfDiscount, setWhatIfDiscount] = useState('');
  const [whatIfHoliday, setWhatIfHoliday] = useState('');
  const [whatIfWeather, setWhatIfWeather] = useState('');
  // Corrected state initialization for numerical inputs to avoid `NaN` issues if input is empty
  const [whatIfPrice, setWhatIfPrice] = useState('');
  const [whatIfCompetitorPricing, setWhatIfCompetitorPricing] = useState('');


  const handleFetchForecast = async () => {
    clearMessages();
    if (!storeId || !productId) {
      setError('Please enter both Store ID and Product ID to get a forecast.');
      return;
    }
    if (numDays <= 0) {
      setError('Number of days to forecast must be positive.');
      return;
    }

    const whatIfParams = {
        ...(whatIfDiscount !== '' && { future_discount: parseFloat(whatIfDiscount) }),
        ...(whatIfHoliday !== '' && whatIfHoliday !== 'Select...' && { future_holiday: whatIfHoliday }),
        ...(whatIfWeather !== '' && whatIfWeather !== 'Select...' && { future_weather: whatIfWeather }),
        ...(whatIfPrice !== '' && { future_price: parseFloat(whatIfPrice) }),
        ...(whatIfCompetitorPricing !== '' && { future_competitor_pricing: parseFloat(whatIfCompetitorPricing) }),
    };


    try {
      const data = await getDemandForecast(storeId, productId, numDays, whatIfParams);
      setForecastData(data);
      if (data.length > 0) {
        setMessage(`Successfully fetched demand forecast for ${data.length} days.`);
      } else {
        setMessage('No forecast data available for the specified product and store.');
      }
      setReorderRecommendation(null); // Clear previous reorder recommendation when fetching new forecast
    } catch (err) {
      setError(err.message || 'Failed to fetch demand forecast.');
      setForecastData([]);
      setReorderRecommendation(null);
    }
  };

  const handleExportForecastCSV = () => {
    if (forecastData.length === 0) {
      alert("No forecast data to export.");
      return;
    }
    downloadCSV(forecastData, `demand_forecast_${storeId}_${productId}_${numDays}days.csv`);
    setMessage('Demand forecast exported to CSV.');
  };

  const handleFetchReorderRecommendation = async () => {
    clearMessages();
    if (!storeId || !productId) {
        setError('Please enter both Store ID and Product ID to get reorder recommendations.');
        return;
    }
    try {
        const recommendation = await getReorderRecommendation(storeId, productId);
        setReorderRecommendation(recommendation);
        setMessage('Reorder recommendation fetched successfully.');
    } catch (err) {
        setError(err.message || 'Failed to fetch reorder recommendation.');
        setReorderRecommendation(null);
    }
  };


  return (
    <section className="page-content">
      <h1>Demand Forecasting & Reorder Recommendations</h1>

      {/* Demand Forecast Configuration Section */}
      <div className="card">
        <h2>Configure Demand Forecast</h2>
        <p className="hint">Enter product and store details to generate a sales forecast for future days.</p>
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
            Number of Days to Forecast:
            <input
              type="number"
              value={numDays}
              onChange={(e) => setNumDays(parseInt(e.target.value) || 0)}
              placeholder="e.g., 30"
            />
          </label>
          {/* Moved Export CSV button here */}
          <button onClick={handleFetchForecast}>Get Demand Forecast</button>
          <button onClick={handleExportForecastCSV} disabled={forecastData.length === 0}>Export CSV</button>
        </div>
      </div>

      {/* Demand Drivers (Scenario Analysis) Inputs Section */}
      <div className="card" style={{ marginTop: '20px' }}>
          <h2>Demand Drivers (Scenario Analysis)</h2>
          <p className="hint">Adjust these factors and click "Get Demand Forecast" again to see how they might impact future sales predictions.</p>
          <div className="input-group">
              <label>
                  Future Discount (%):
                  <input type="number" step="0.01" value={whatIfDiscount} onChange={(e) => setWhatIfDiscount(e.target.value)} placeholder="e.g., 0.1 (for 10%)" />
              </label>
              <label>
                  Future Holiday/Promotion:
                  <select value={whatIfHoliday} onChange={(e) => setWhatIfHoliday(e.target.value)}>
                    <option value="">Select...</option>
                    <option value="No">No</option>
                    <option value="Holiday Sale">Holiday Sale</option>
                    <option value="Festival Promotion">Festival Promotion</option>
                    <option value="Seasonal Discount">Seasonal Discount</option>
                  </select>
              </label>
              <label>
                  Future Weather Condition:
                  <select value={whatIfWeather} onChange={(e) => setWhatIfWeather(e.target.value)}>
                    <option value="">Select...</option>
                    <option value="Clear">Clear</option>
                    <option value="Cloudy">Cloudy</option>
                    <option value="Rainy">Rainy</option>
                    <option value="Snowy">Snowy</option>
                  </select>
              </label>
              <label>
                  Future Price ($):
                  <input type="number" step="0.01" value={whatIfPrice} onChange={(e) => setWhatIfPrice(e.target.value)} placeholder="e.g., 12.99" />
              </label>
              <label>
                  Future Competitor Pricing ($):
                  <input type="number" step="0.01" value={whatIfCompetitorPricing} onChange={(e) => setWhatIfCompetitorPricing(e.target.value)} placeholder="e.g., 11.50" />
              </label>
          </div>
      </div>

      {/* Demand Forecast Results Display */}
      {forecastData.length > 0 && (
        <div className="card forecast-results" style={{ marginTop: '20px' }}>
          <h2>Predicted Daily Demand Forecast</h2>
          <p className="hint">Visual representation and daily breakdown of the forecasted demand.</p>
          <div className="chart-container-recharts" style={{ marginBottom: '20px' }}>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={forecastData} margin={{ top: 10, right: 30, left: 20, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" angle={-45} textAnchor="end" interval="preserveStartEnd" height={70} />
                <YAxis label={{ value: 'Predicted Units', angle: -90, position: 'insideLeft' }} />
                <Tooltip content={<ForecastTooltip />} />
                <Legend />
                <Line type="monotone" dataKey="predicted_demand" stroke="#8884d8" activeDot={{ r: 8 }} name="Predicted Demand" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h3>Daily Forecast Details:</h3>
          <div className="scrollable-list-container">
            <ul className="forecast-list alert-list">
              {forecastData.map((data, index) => (
                <li key={index} className="forecast-item alert-item">
                  <p><strong>Date:</strong> {data.date}</p>
                  <p><strong>Predicted Demand:</strong> {data.predicted_demand} units</p>
                  <p>For Product ID: {data.product_id} at Store ID: {data.store_id}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {forecastData.length === 0 && storeId && productId && (
        <p className="no-forecast-message" style={{ marginTop: '20px' }}>No demand forecast available. Please enter criteria and click 'Get Demand Forecast'.</p>
      )}


      {/* Reorder Recommendation Section */}
      <div className="card" style={{ marginTop: '25px' }}>
          <h2>Reorder Recommendations</h2>
          <p className="hint">Get smart recommendations on when and how much to reorder based on demand forecast and lead times.</p>
          <div className="input-group">
              <button onClick={handleFetchReorderRecommendation} disabled={!storeId || !productId}>
                  Get Reorder Recommendation
              </button>
          </div>
          {reorderRecommendation && (
              <div className="reorder-display inventory-display" style={{ marginTop: '20px' }}>
                  <h3>Recommendation for <span className="highlight-text">{reorderRecommendation.product_id}</span> @ <span className="highlight-text">{reorderRecommendation.store_id}</span>:</h3>
                  <p><strong>Current Stock:</strong> {reorderRecommendation.current_stock} units</p>
                  <p><strong>Min. Replenish Time:</strong> {reorderRecommendation.min_replenish_time_days} days</p>
                  <p><strong>Average Daily Forecasted Demand:</strong> {reorderRecommendation.average_daily_forecasted_demand} units</p>
                  <p><strong>Safety Stock:</strong> {reorderRecommendation.safety_stock_units} units</p>
                  <p><strong>Reorder Point:</strong> {reorderRecommendation.reorder_point_units} units</p>
                  <p><strong>Reorder Needed:</strong> <span style={{ fontWeight: 'bold', color: reorderRecommendation.reorder_needed === 'Yes' ? '#c0392b' : '#28a745' }}>{reorderRecommendation.reorder_needed}</span></p>
                  <p><strong>Suggested Order Quantity:</strong> {reorderRecommendation.suggested_order_quantity} units</p>
                  <p><strong>Suggested Order Date:</strong> {reorderRecommendation.suggested_order_date}</p>
                  <p><strong>Suggested Delivery Date:</strong> {reorderRecommendation.suggested_delivery_date}</p>
                  <p className="hint" style={{ marginTop: '10px' }}>{reorderRecommendation.notes}</p>
              </div>
          )}
          {reorderRecommendation === null && storeId && productId && (
              <p className="no-reorder-message" style={{ marginTop: '20px' }}>Click "Get Reorder Recommendation" to see suggestions based on your forecast.</p>
          )}
          {reorderRecommendation === null && (!storeId || !productId) && (
              <p className="no-reorder-message" style={{ marginTop: '20px' }}>Please enter Store ID and Product ID above to get reorder recommendations.</p>
          )}
      </div>
    </section>
  );
}

export default DemandForecastPage;
