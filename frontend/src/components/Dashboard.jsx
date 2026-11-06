
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import FraudRingGraph from './FraudRingGraph.jsx';
import StatsCard from './StatsCard.jsx';
import './Dashboard.css';

const API_URL = 'http://localhost:3000';

function Dashboard() {
  const [fraudRings, setFraudRings] = useState([]);
  const [selectedRing, setSelectedRing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchFraudRings = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await axios.get(
          `${API_URL}/api/dashboard/fraud-rings`
        );

        const data = response.data;

        // Support common API response formats
        const rings = Array.isArray(data)
          ? data
          : data.fraud_rings || data.rings || data.data || [];

        if (!Array.isArray(rings)) {
          throw new Error('Invalid fraud-ring response from server.');
        }

        setFraudRings(rings);
        setSelectedRing(rings[0] || null);
      } catch (err) {
        console.error('Dashboard API error:', err);

        setError(
          err.response?.data?.error ||
          err.message ||
          'Unable to load fraud rings.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchFraudRings();
  }, []);

  const totalMerchants = fraudRings.reduce(
    (sum, ring) => sum + (Number(ring.size) || ring.merchants?.length || 0),
    0
  );

  const largestRing = fraudRings.reduce(
    (max, ring) =>
      Math.max(max, Number(ring.size) || ring.merchants?.length || 0),
    0
  );

  if (loading) {
    return (
      <div className="dashboard container">
        <h2>Loading fraud rings...</h2>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard container">
        <h2>Top Fraud Rings Dashboard</h2>
        <p style={{ color: 'red' }}>Error: {error}</p>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h2>Top Fraud Rings Dashboard</h2>
          <p className="subtitle">
            Visualization of fraud networks detected by the ML service
          </p>
        </div>

        <div className="stats-grid">
          <StatsCard
            title="Total Fraud Rings"
            value={fraudRings.length}
            icon="🔗"
            color="#ef4444"
          />

          <StatsCard
            title="Largest Ring Size"
            value={largestRing}
            icon="👥"
            color="#dc2626"
          />

          <StatsCard
            title="Total Fraudulent Merchants"
            value={totalMerchants}
            icon="⚠️"
            color="#991b1b"
          />
        </div>

        {fraudRings.length === 0 ? (
          <div className="card">
            <h3>No fraud rings found.</h3>
          </div>
        ) : (
          <>
            <div className="card">
              <h3 className="card-title">
                Select Fraud Ring to Visualize
              </h3>

              <div className="ring-selector">
                {fraudRings.map((ring, index) => (
                  <button
                    key={ring.ring_id || index}
                    className={`ring-button ${
                      selectedRing?.ring_id === ring.ring_id
                        ? 'active'
                        : ''
                    }`}
                    onClick={() => setSelectedRing(ring)}
                  >
                    <div className="ring-button-title">
                      {ring.ring_id || `Ring #${index + 1}`}
                    </div>

                    <div className="ring-button-size">
                      {ring.size || ring.merchants?.length || 0} merchants
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {selectedRing && (
              <div className="card">
                <h3 className="card-title">
                  Fraud Ring Network —{' '}
                  {selectedRing.size || selectedRing.merchants?.length || 0}{' '}
                  Merchants Connected
                </h3>

                <FraudRingGraph data={selectedRing} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
