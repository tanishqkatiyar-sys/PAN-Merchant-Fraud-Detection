
const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');

// Load environment variables from project root
require('dotenv').config({
  path: path.resolve(__dirname, '../../../.env')
});

const app = express();
const PORT = process.env.NODE_PORT || 3000;

// Python ML service URL
const PYTHON_SERVICE_URL =
  process.env.PYTHON_SERVICE_URL || 'http://localhost:5000';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 1. Health check
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    status: 'healthy',
    service: 'node-api-service'
  });
});

// 2. Get top fraud rings
app.get('/api/dashboard/fraud-rings', async (req, res) => {
  try {
    const response = await axios.get(
      `${PYTHON_SERVICE_URL}/api/top-fraud-rings`
    );

    res.json(response.data);
  } catch (error) {
    console.error('Fraud rings error:', error.message);

    res.status(error.response?.status || 500).json({
      success: false,
      error: 'Failed to fetch fraud rings',
      details: error.response?.data || error.message
    });
  }
});

// 3. Search merchant by ID
app.post('/api/search', async (req, res) => {
  try {
    const { merchant_id } = req.body;

    if (!merchant_id || !merchant_id.trim()) {
      return res.status(400).json({
        success: false,
        error: 'Merchant ID is required'
      });
    }

    console.log('Search request received:', merchant_id);

    const response = await axios.post(
      `${PYTHON_SERVICE_URL}/api/search`,
      { merchant_id: merchant_id.trim() }
    );

    return res.status(response.status).json(response.data);

  } catch (error) {
    console.error(
      'Merchant search error:',
      error.response?.data || error.message
    );

    return res.status(error.response?.status || 500).json({
      success: false,
      error: 'Search failed',
      details: error.response?.data || error.message
    });
  }
});

// 4. Get merchant details
app.get('/api/merchant/:merchant_id', async (req, res) => {
  try {
    const merchantId = req.params.merchant_id;

    const response = await axios.get(
      `${PYTHON_SERVICE_URL}/api/merchant/${encodeURIComponent(merchantId)}`
    );

    res.json(response.data);

  } catch (error) {
    console.error('Merchant details error:', error.message);

    res.status(error.response?.status || 500).json({
      success: false,
      error: 'Failed to fetch merchant details',
      details: error.response?.data || error.message
    });
  }
});

// 5. Analytics summary
app.get('/api/analytics/summary', (req, res) => {
  res.json({
    success: true,
    data: {
      searches_last_24h: 0,
      recent_searches: []
    }
  });
});

// 6. 404 handler - keep this AFTER all API routes
app.use((req, res) => {
  console.log('Route not found:', req.method, req.originalUrl);

  res.status(404).json({
    success: false,
    error: 'Route not found',
    method: req.method,
    path: req.originalUrl
  });
});

// 7. Global error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);

  res.status(500).json({
    success: false,
    error: 'Internal server error'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Node API Service running on port ${PORT}`);
  console.log(`Python ML Service URL: ${PYTHON_SERVICE_URL}`);
  console.log('POST /api/search registered successfully');
});

module.exports = app;
