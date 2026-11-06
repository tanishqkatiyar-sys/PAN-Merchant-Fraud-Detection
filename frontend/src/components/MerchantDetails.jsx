
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import FraudRingGraph from './FraudRingGraph.jsx';
import SimilarFraudsList from './SimilarFraudsList.jsx';
import './MerchantDetails.css';

function MerchantDetails() {
  const { merchantId } = useParams();
  const navigate = useNavigate();

  const [merchantData, setMerchantData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMerchantDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        setMerchantData(null);

        // Call the POST API that we tested successfully
        const response = await axios.post(
          'http://localhost:3000/api/search',
          {
            merchant_id: decodeURIComponent(merchantId)
          }
        );

        console.log('Merchant API response:', response.data);

        // Extract merchant information
        const data = response.data;

        if (!data || !data.merchant) {
          setError('Merchant not found. Please check the ID and try again.');
          return;
        }

        // Store the complete response
        setMerchantData(data);

      } catch (err) {
        console.error(
          'Error fetching merchant details:',
          err.response?.data || err.message
        );

        if (err.response?.status === 404) {
          setError('Merchant not found. Please check the ID and try again.');
        } else {
          setError(
            err.response?.data?.error ||
            'Failed to load merchant details. Please try again later.'
          );
        }
      } finally {
        setLoading(false);
      }
    };

    if (merchantId) {
      fetchMerchantDetails();
    }
  }, [merchantId]);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading merchant details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="error-container">
          <div className="error">{error}</div>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/')}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!merchantData?.merchant) {
    return (
      <div className="container">
        <div className="error-container">
          <div className="error">Merchant details are unavailable.</div>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/')}
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { merchant, fraud_ring, similar_frauds } = merchantData;

  const isFraud = Number(merchant.is_fraud) === 1;

  return (
    <div className="merchant-details">
      <div className="container">

        <button
          className="back-button"
          onClick={() => navigate('/')}
        >
          ← Back to Dashboard
        </button>

        {/* Fraud Alert */}
        {isFraud ? (
          <div className="fraud-alert">
            <span className="alert-icon">⚠️</span>
            <span>This merchant has been flagged as FRAUDULENT</span>
          </div>
        ) : (
          <div className="safe-alert">
            <span className="alert-icon">✅</span>
            <span>This merchant appears to be LEGITIMATE</span>
          </div>
        )}

        {/* Merchant Information */}
        <div className="card">
          <h2 className="card-title">Merchant Information</h2>

          <div className="info-grid">

            <div className="info-item">
              <span className="info-label">Merchant ID</span>
              <span className="info-value">{merchant.merchant_id}</span>
            </div>

            <div className="info-item">
              <span className="info-label">PAN Hash</span>
              <span className="info-value">{merchant.pan_hash ?? 'N/A'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">Device Hash</span>
              <span className="info-value">{merchant.device_id_hash ?? 'N/A'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">IP Hash</span>
              <span className="info-value">{merchant.ip_hash ?? 'N/A'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">City</span>
              <span className="info-value">{merchant.city ?? 'N/A'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">Merchant Tier</span>
              <span className="info-value badge">{merchant.merchant_tier ?? 'N/A'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">Category</span>
              <span className="info-value">{merchant.merchant_category ?? 'N/A'}</span>
            </div>

            <div className="info-item">
              <span className="info-label">KYC Verified</span>
              <span className="info-value">
                {merchant.is_kyc_verified ? '✅ Yes' : '❌ No'}
              </span>
            </div>

          </div>
        </div>

        {/* Transaction Metrics */}
        <div className="card">
          <h2 className="card-title">Transaction Metrics</h2>

          <div className="metrics-grid">

            <div className="metric-card">
              <div className="metric-value">
                {merchant.total_txns_90d ?? 'N/A'}
              </div>
              <div className="metric-label">Total Transactions (90d)</div>
            </div>

            <div className="metric-card">
              <div className="metric-value">
                ₹{Number(merchant.avg_txn_value ?? 0).toFixed(2)}
              </div>
              <div className="metric-label">Avg Transaction Value</div>
            </div>

            <div className="metric-card">
              <div className="metric-value">
                {(Number(merchant.chargeback_rate ?? 0) * 100).toFixed(2)}%
              </div>
              <div className="metric-label">Chargeback Rate</div>
            </div>

            <div className="metric-card">
              <div className="metric-value">
                {(Number(merchant.refund_ratio ?? 0) * 100).toFixed(2)}%
              </div>
              <div className="metric-label">Refund Ratio</div>
            </div>

          </div>
        </div>

        {/* Shared Identifiers */}
        <div className="card">
          <h2 className="card-title">Shared Identifiers (Red Flags)</h2>

          <div className="metrics-grid">

            <div className="metric-card">
              <div className="metric-value">
                {merchant.shared_pan_count ?? 'N/A'}
              </div>
              <div className="metric-label">Shared PAN Count</div>
            </div>

            <div className="metric-card">
              <div className="metric-value">
                {merchant.shared_device_count ?? 'N/A'}
              </div>
              <div className="metric-label">Shared Device Count</div>
            </div>

            <div className="metric-card">
              <div className="metric-value">
                {merchant.shared_ip_count ?? 'N/A'}
              </div>
              <div className="metric-label">Shared IP Count</div>
            </div>

          </div>
        </div>

        {/* Fraud Ring Network */}
        {fraud_ring && fraud_ring.nodes && (
          <div className="card">
            <h2 className="card-title">
              Fraud Network - {fraud_ring.nodes.length} Connected Merchants
            </h2>
            <FraudRingGraph data={fraud_ring} />
          </div>
        )}

        {/* Similar Frauds */}
        {similar_frauds && similar_frauds.length > 0 && (
          <div className="card">
            <h2 className="card-title">
              Top 10 Similar Fraudulent Merchants (Cosine Similarity)
            </h2>
            <SimilarFraudsList frauds={similar_frauds} />
          </div>
        )}

      </div>
    </div>
  );
}

export default MerchantDetails;
