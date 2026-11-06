
import React, { useRef, useEffect, useState, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import './FraudRingGraph.css';

function FraudRingGraph({ data }) {
  const graphRef = useRef();
  const [hoveredNode, setHoveredNode] = useState(null);
  const [dimensions, setDimensions] = useState({
    width: 800,
    height: 600
  });

  // Update graph dimensions
  useEffect(() => {
    const updateDimensions = () => {
      const container = document.querySelector('.graph-container');

      if (container) {
        setDimensions({
          width: container.offsetWidth || 800,
          height: Math.min(600, window.innerHeight * 0.6)
        });
      }
    };

    updateDimensions();

    window.addEventListener('resize', updateDimensions);

    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);

  // Prepare graph data
  const graphData = useMemo(() => {
    if (!data || !Array.isArray(data.nodes)) {
      return { nodes: [], links: [] };
    }

    const edges = data.edges || data.links || [];

    return {
      nodes: data.nodes.map(node => ({
        ...node,
        id: node.id ?? node.merchant_id,
        color: '#ef4444'
      })),

      links: edges.map(edge => ({
        ...edge,
        source: edge.source,
        target: edge.target,
        value: Number(edge.weight) || 1,
        reason: edge.reason
      }))
    };
  }, [data]);

  const handleNodeHover = (node) => {
    setHoveredNode(node || null);
  };

  // Open merchant details when clicking a node
  const handleNodeClick = (node) => {
    if (node) {
      const id = node.merchant_id || node.id;

      if (id) {
        window.open(
          `/merchant/${encodeURIComponent(id)}`,
          '_blank'
        );
      }
    }
  };

  if (!data || !graphData.nodes.length) {
    return <p>No fraud network data available.</p>;
  }

  return (
    <div className="fraud-ring-graph">

      <div className="graph-container">

        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}

          nodeLabel={node => node.merchant_id || node.id}

          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.merchant_id || node.id;
            const fontSize = 12 / globalScale;

            ctx.font = `${fontSize}px Sans-Serif`;

            // Draw node circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);

            ctx.fillStyle =
              hoveredNode?.id === node.id
                ? '#dc2626'
                : '#ef4444';

            ctx.fill();

            // Draw label when hovered
            if (hoveredNode?.id === node.id) {
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = '#fca5a5';
              ctx.fillText(label, node.x, node.y - 10);
            }
          }}

          linkWidth={link => Math.max(1, Number(link.value) || 1)}

          linkColor={() => 'rgba(239, 68, 68, 0.3)'}

          onNodeHover={handleNodeHover}

          onNodeClick={handleNodeClick}

          cooldownTicks={100}

          onEngineStop={() => {
            graphRef.current?.zoomToFit(400);
          }}
        />

      </div>

      {hoveredNode && (
        <div className="node-tooltip">

          <div className="tooltip-header">
            Merchant Details
          </div>

          <div className="tooltip-row">
            <span className="tooltip-label">ID:</span>
            <span className="tooltip-value">
              {hoveredNode.merchant_id || hoveredNode.id}
            </span>
          </div>

          <div className="tooltip-row">
            <span className="tooltip-label">PAN Hash:</span>
            <span className="tooltip-value">
              {hoveredNode.pan_hash || 'N/A'}
            </span>
          </div>

          <div className="tooltip-row">
            <span className="tooltip-label">Tier:</span>
            <span className="tooltip-value">
              {hoveredNode.merchant_tier || 'N/A'}
            </span>
          </div>

          <div className="tooltip-row">
            <span className="tooltip-label">City:</span>
            <span className="tooltip-value">
              {hoveredNode.city || 'N/A'}
            </span>
          </div>

          <div className="tooltip-footer">
            Click to view full details
          </div>

        </div>
      )}

    </div>
  );
}

export default FraudRingGraph;
