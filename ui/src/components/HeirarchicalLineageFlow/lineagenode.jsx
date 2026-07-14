import React, { useState } from "react";
import { Handle, Position } from "reactflow";

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

const getBadgeLabel = (type) => {
  if (type === "Environment") return "PIPELINE_NAME";
  return type ? type.toUpperCase() : "NODE";
};

const LineageNode1 = ({ data }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const { backgroundColor, fullUuid, ...rest } = data;
  const tooltipData = { ...rest, uuid: fullUuid || data.uuid };

  return (
    <div
      className="lineage-card"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      style={{ position: "relative" }}
    >
      <Handle type="target" position={Position.Top} />

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

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default LineageNode1;