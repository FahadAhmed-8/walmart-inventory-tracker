    // frontend/src/api/inventoryApi.js

    // Reads the backend URL from the .env file (REACT_APP_BACKEND_URL)
    // Defaults to http://localhost:5000 if not set (e.g., in a development environment)
    const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

    // Function to get inventory for a specific product at a specific store
    export const getInventory = async (storeId, productId) => {
        try {
            // Construct the URL for the GET request
            const response = await fetch(`${BACKEND_URL}/inventory/${storeId}/${productId}`);
            
            // Check if the HTTP response was successful (status code 200-299)
            if (!response.ok) {
                // If not successful, parse the error message from the backend
                const errorData = await response.json();
                throw new Error(errorData.message || errorData.error || 'Failed to fetch inventory');
            }
            // If successful, parse and return the JSON data
            return await response.json();
        } catch (error) {
            console.error("Error fetching inventory:", error);
            // Re-throw the error so calling components can handle it
            throw error;
        }
    };

    // Function to record a sale
    export const recordSale = async (storeId, productId, quantity) => {
        try {
            const response = await fetch(`${BACKEND_URL}/inventory/sale`, {
                method: 'POST', // Use POST method for creating/modifying data
                headers: {
                    'Content-Type': 'application/json', // Indicate that we're sending JSON data
                },
                // Convert JavaScript object to JSON string for the request body
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

    // Function to record a receipt (incoming stock)
    export const recordReceipt = async (storeId, productId, quantity) => {
        try {
            const response = await fetch(`${BACKEND_URL}/inventory/receipt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
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

    // Function to get low stock alerts
    export const getLowStockAlerts = async (daysLeft, storeId = '') => {
        // Build the URL with query parameters
        let url = `${BACKEND_URL}/inventory/low_stock_alerts?days_left=${daysLeft}`;
        if (storeId) {
            url += `&store_id=${storeId}`; // Add store_id if provided
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

    // Function to upload a CSV file for sales batch
    export const uploadSalesCSV = async (file) => {
        const formData = new FormData(); // FormData is used for file uploads
        formData.append('file', file); // 'file' matches the name expected by Flask's request.files
        try {
            const response = await fetch(`${BACKEND_URL}/inventory/sale_batch`, {
                method: 'POST',
                body: formData, // When using FormData, fetch automatically sets 'Content-Type': 'multipart/form-data'
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

    // Function to upload a CSV file for receipts batch
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
    