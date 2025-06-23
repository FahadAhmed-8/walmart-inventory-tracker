// frontend/src/pages/InventoryActionsPage.js
import React, { useState } from 'react';
import { getInventory, recordSale, recordReceipt, uploadSalesCSV, uploadReceiptsCSV } from '../api/inventoryApi';

function InventoryActionsPage({ setMessage, setError, clearMessages }) {
  const [storeId, setStoreId] = useState('');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('');
  const [inventoryData, setInventoryData] = useState(null);
  const [selectedSalesFile, setSelectedSalesFile] = useState(null);
  const [selectedReceiptsFile, setSelectedReceiptsFile] = useState(null);

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
      fetchInventory(); // Refresh inventory after sale
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
      fetchInventory(); // Refresh inventory after receipt
    } catch (err) {
      setError(err.message || 'Failed to record receipt.');
    }
  };

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
      // Optionally, refetch inventory for all impacted products if this was a small batch.
      // For large batches, it's inefficient to refetch all.
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
      // Optionally, refetch inventory for all impacted products.
    } catch (err) {
      setError(err.message || 'Failed to upload receipts CSV.');
    }
  };

  return (
    <> {/* Fragment to return multiple elements */}
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
    </>
  );
}

export default InventoryActionsPage;
