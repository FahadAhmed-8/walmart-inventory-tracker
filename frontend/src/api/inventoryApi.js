// frontend/src/api/inventoryApi.js

const API_BASE_URL = 'http://localhost:5000/inventory';

export const getInventory = async (storeId, productId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/${storeId}/${productId}`);
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching inventory:", error);
    throw error;
  }
};

export const recordSale = async (storeId, productId, quantity) => {
  try {
    const response = await fetch(`${API_BASE_URL}/sale`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ store_id: storeId, product_id: productId, quantity }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error recording sale:", error);
    throw error;
  }
};

export const recordReceipt = async (storeId, productId, quantity) => {
  try {
    const response = await fetch(`${API_BASE_URL}/receipt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ store_id: storeId, product_id: productId, quantity }),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error recording receipt:", error);
    throw error;
  }
};

export const getLowStockAlerts = async (daysLeftThreshold, storeId = '') => {
  try {
    const url = new URL(`${API_BASE_URL}/low_stock_alerts`);
    url.searchParams.append('days_left', daysLeftThreshold);
    if (storeId) {
      url.searchParams.append('store_id', storeId);
    }
    const response = await fetch(url.toString());
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching low stock alerts:", error);
    throw error;
  }
};

// NEW: API call for overstocked alerts
export const getOverstockedAlerts = async (thresholdMultiplier, daysForDemand, storeId = '') => {
  try {
    const url = new URL(`${API_BASE_URL}/overstocked_alerts`);
    url.searchParams.append('threshold_multiplier', thresholdMultiplier);
    url.searchParams.append('days_for_demand', daysForDemand);
    if (storeId) {
      url.searchParams.append('store_id', storeId);
    }
    const response = await fetch(url.toString());
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching overstocked alerts:", error);
    throw error;
  }
};


export const uploadSalesCSV = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/sale_batch`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error uploading sales CSV:", error);
    throw error;
  }
};

export const uploadReceiptsCSV = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/receipt_batch`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error uploading receipts CSV:", error);
    throw error;
  }
};

// NEW: Generic CSV download helper
export const downloadCSV = (data, filename) => {
  if (!data || data.length === 0) {
    alert("No data to export."); // Changed from window.alert to standard alert for consistency
    return;
  }

  // Get headers from the first object
  const headers = Object.keys(data[0]);
  const csvRows = [];
  csvRows.push(headers.join(',')); // Add header row

  // Add data rows
  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header];
      // Handle commas or newlines in data by enclosing in quotes
      return `"${String(value).replace(/"/g, '""')}"`;
    });
    csvRows.push(values.join(','));
  }

  const csvString = csvRows.join('\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
