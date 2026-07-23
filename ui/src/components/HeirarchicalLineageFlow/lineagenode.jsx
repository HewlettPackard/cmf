import React, { useState } from "react";
import { Handle, Position } from "reactflow";

// Actual node color scheme for the lineage tree, matching the MiniMap color rules

const getColor = (type) => {
  switch (type) {
    case "Dataset":
      return "#10b981";

    case "Execution":
      return "#3b82f6";

    case "Node":
    case "Metrics":
      return "#ef4444";

    case "Model":
    case "Stage":
      return "#f59e0b";

    case "Environment":
      return "#14b8a6";
      
    default:
      return "#64748b";
  }
};

// Return the label to show the node's badge based on its type.
const getBadgeLabel = (type) => {
  if (type === "Environment") return "PIPELINE_NAME";
  return type ? type.toUpperCase() : "NODE";
};

// A style object that visually hide the connector dots for execution nodes.
const HANDLE_HIDDEN_STYLE = {
  opacity: 0,
  width: 1,
  height: 1,
  minWidth: 0,
  minHeight: 0,
  border: "none",
  background: "transparent",
};

// A custom node component which track shows a tooltip state for hover.
// Bascically,custom node component.
const LineageNode1 = ({ data }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const { backgroundColor, fullUuid, ...rest } = data;
  const tooltipData = { ...rest, uuid: fullUuid || data.uuid };

  // Only hide the connector dots on Execution node boxes;
  // Pipeline and Stage nodes keep their default visible handles
  const isExecution = data.type === "Execution";
  const targetHandleStyle = isExecution ? HANDLE_HIDDEN_STYLE : undefined;
  const sourceHandleStyle = isExecution ? HANDLE_HIDDEN_STYLE : undefined;

  return (
    <div
      className="lineage-card"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      style={{ position: "relative" }}
    >
      <Handle type="target" position={Position.Top} style={targetHandleStyle} />

      <div className="lineage-badge" style={{ backgroundColor: getColor(data.type) }}>
        {getBadgeLabel(data.type)}
      </div>

      <div className="lineage-title">{data.name}</div>

      {data.uuid && <div className="lineage-subtitle">{data.uuid}</div>}

      {showTooltip && (
        <pre className="lineage-tooltip">
          {JSON.stringify(tooltipData, null, 2)}
        </pre>
      )}

      <Handle type="source" position={Position.Bottom} style={sourceHandleStyle} />
    </div>
  );
};

export default LineageNode1;