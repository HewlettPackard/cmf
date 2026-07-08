import React from "react";
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

const LineageNode1 = ({ data }) => {
  return (
    <div
      className="lineage-card"
      title={JSON.stringify(data, null, 2)}
    >
      <Handle type="target" position={Position.Top} />



      <div
        className="lineage-badge"
        style={{
          backgroundColor: getColor(data.type),
        }}
      >
          {data.type ? data.type.toUpperCase() : "NODE"}
      </div>

  

      <div className="lineage-title">
        {data.name}
      </div>

      {data.uuid && (
        <div className="lineage-subtitle">
          {data.uuid}
        </div>
      )}

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default LineageNode1;