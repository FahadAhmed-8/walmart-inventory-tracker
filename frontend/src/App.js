// frontend/src/App.js (Multipage Navigation)
import React, { useState } from 'react';
import './App.css';
import InventoryActionsPage from './pages/InventoryActionsPage';
import AlertsAndOverstockPage from './pages/AlertsAndOverstockPage';
import DemandForecastPage from './pages/DemandForecastPage'; // NEW: Import DemandForecastPage
import OptimalStockingPage from './pages/OptimalStockingPage';

function App() {
  const [currentPage, setCurrentPage] = useState('inventoryActions');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const clearMessages = () => {
    setMessage('');
    setError('');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'inventoryActions':
        return (
          <InventoryActionsPage
            setMessage={setMessage}
            setError={setError}
            clearMessages={clearMessages}
          />
        );
      case 'alertsAndOverstock':
        return (
          <AlertsAndOverstockPage
            setMessage={setMessage}
            setError={setError}
            clearMessages={clearMessages}
          />
        );
      case 'demandForecast': // NEW Case for Demand Forecast Page
        return (
          <DemandForecastPage
            setMessage={setMessage}
            setError={setError}
            clearMessages={clearMessages}
          />
        );
      case 'optimalStocking': // NEW Case for Optimal Stocking Page
        return (
          <OptimalStockingPage
            setMessage={setMessage}
            setError={setError}
            clearMessages={clearMessages}
          />
        );
      default:
        return (
          <InventoryActionsPage
            setMessage={setMessage}
            setError={setError}
            clearMessages={clearMessages}
          />
        );
    }
  };

  return (
    <div className="App">
      <h1>Walmart Inventory Tracker</h1>

  <nav className="main-nav">
    <button
      onClick={() => setCurrentPage('inventoryActions')}
      className={currentPage === 'inventoryActions' ? 'active' : ''}
    >
      Inventory Operations
    </button>
    <button
      onClick={() => setCurrentPage('alertsAndOverstock')}
      className={currentPage === 'alertsAndOverstock' ? 'active' : ''}
    >
      Insights & Alerts
    </button>
    <button
      onClick={() => setCurrentPage('demandForecast')}
      className={currentPage === 'demandForecast' ? 'active' : ''}
    >
      Demand Forecast
    </button>
    <button
      onClick={() => setCurrentPage('optimalStocking')} // NEW Button
      className={currentPage === 'optimalStocking' ? 'active' : ''}
    >
      Optimal Stocking
    </button>
  </nav>

      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}

      {renderPage()}
    </div>
  );
}

export default App;
