
import React, { useState } from 'react';
import FraudRingGraph from './FraudRingGraph.jsx';
import StatsCard from './StatsCard.jsx';
import './Dashboard.css';

// Sample data for the frontend demonstration.
// No backend or database connection is required.
const sampleFraudRings = [
  {
    ring_id: 'RING-001',
    size: 6,
    merchants: [
      { id: 'M001', name: 'Merchant A' },
      { id: 'M002', name: 'Merchant B' },
      { id: 'M003', name: 'Merchant C' },
      { id: 'M004', name: 'Merchant D' },
      { id: 'M005', name: 'Merchant E' },
      { id: 'M006', name: 'Merchant F' }
    ],
    nodes: [
      { id: 'M001', label: 'Merchant A' },
      { id: 'M002', label: 'Merchant B' },
      { id: 'M003', label: 'Merchant C' },
      { id: 'M004', label: 'Merchant D' },
      { id: 'M005', label: 'Merchant E' },
      { id: 'M006', label: 'Merchant F' }
    ],
    edges: [
      { source: 'M001', target: 'M002' },
      { source: 'M002', target: 'M003' },
      { source: 'M003', target: 'M004' },
      { source: 'M004', target: 'M005' },
      { source: 'M005', target: 'M006' },
      { source: 'M006', target: 'M001' }
    ]
  },
  {
    ring_id: 'RING-002',
    size: 4,
    merchants: [
      { id: 'M007', name: 'Merchant G' },
      { id: 'M008', name: 'Merchant H' },
      { id: 'M009', name: 'Merchant I' },
      { id: 'M010', name: 'Merchant J' }
    ],
    nodes: [
      { id: 'M007', label: 'Merchant G' },
      { id: 'M008', label: 'Merchant H' },
      { id: 'M009', label: 'Merchant I' },
      { id: 'M010', label: 'Merchant J' }
    ],
    edges: [
      { source: 'M007', target: 'M008' },
      { source: 'M008', target: 'M009' },
      { source: 'M009', target: 'M010' },
      { source: 'M010', target: 'M007' }
    ]
  },
  {
    ring_id: 'RING-003',
    size: 3,
    merchants: [
      { id: 'M011', name: 'Merchant K' },
      { id: 'M012', name: 'Merchant L' },
      { id: 'M013', name: 'Merchant M' }
    ],
    nodes: [
      { id: 'M011', label: 'Merchant K' },
      { id: 'M012', label: 'Merchant L' },
      { id: 'M013', label: 'Merchant M' }
    ],
    edges: [
      { source: 'M011', target: 'M012' },
      { source: 'M012', target: 'M013' },
      { source: 'M013', target: 'M011' }
    ]
  }
];

function Dashboard() {
  const [fraudRings] = useState(sampleFraudRings);
  const [selectedRing, setSelectedRing] = useState(sampleFraudRings[0]);

  const totalMerchants = fraudRings.reduce(
    (sum, ring) => sum + ring.size,
    0
  );

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h2>Top Fraud Rings Dashboard</h2>
          <p className="subtitle">
            Visualization of the largest fraud networks detected
          </p>
          <p className="demo-notice">
            Demo Mode — displaying sample data. Database connection is disabled.
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
            value={Math.max(...fraudRings.map((ring) => ring.size))}
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

        <div className="card">
          <h3 className="card-title">
            Select Fraud Ring to Visualize
          </h3>

          <div className="ring-selector">
            {fraudRings.map((ring, index) => (
              <button
                key={ring.ring_id}
                className={`ring-button ${
                  selectedRing?.ring_id === ring.ring_id ? 'active' : ''
                }`}
                onClick={() => setSelectedRing(ring)}
              >
                <div className="ring-button-title">
                  Ring #{index + 1}
                </div>
                <div className="ring-button-size">
                  {ring.size} merchants
                </div>
              </button>
            ))}
          </div>
        </div>

        {selectedRing && (
          <div className="card">
            <h3 className="card-title">
              Fraud Ring Network — {selectedRing.size} Merchants Connected
            </h3>
            <FraudRingGraph data={selectedRing} />
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
