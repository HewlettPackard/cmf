/***
 * Copyright (2023) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

/**
 * LineageNode Custom Component for React Flow Canvas
 * Renders a standardized custom node layout used for pipeline and graph visualization.
 * 
 * Key Functions & Features:
 * - Dynamic Styling (`getColor`): Maps specific color schemes to node types (Dataset, Execution, Stage, etc.).
 * - Badge Classification (`getBadgeLabel`): Generates localized text labels for metadata visual categorization tags.
 * - Interactive Tooltips (`showTooltip`): Exposes raw node parameters as a pretty-printed JSON overlay on hover.
 * - Clean Edge Layouts (`HANDLE_HIDDEN_STYLE`): Automatically collapses connection handle points exclusively for 
 *   "Execution" nodes to eliminate layout line clutter, while maintaining default connectivity ports on pipeline wrappers.
 */

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

    case "Pipeline":
      return "#14b8a6";
      
    default:
      return "#64748b";
  }
};

// Return the label to show the node's badge based on its type.
const getBadgeLabel = (type) => {
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
const LineageNode = ({ data }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const { backgroundColor, fullUuid, id, tooltipInteraction, ...rest } = data;
  const tooltipData = {...rest, uuid: fullUuid || data.uuid,};
  const isFlatLineage = tooltipInteraction === "flat";
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
      onPointerEnter={() => setShowTooltip(true)}
      onPointerLeave={() => setShowTooltip(false)}
      style={{ position: "relative", pointerEvents: isFlatLineage ? "all" : undefined }}
    >
      <Handle type="target" position={Position.Top} style={targetHandleStyle} />

      <div className="lineage-badge" style={{ backgroundColor: getColor(data.type) }}>
        {getBadgeLabel(data.type)}
      </div>

      <div className="lineage-title">{data.name}</div>

      {data.uuid && <div className="lineage-subtitle">{data.uuid}</div>}

      {showTooltip && (
        <pre className="lineage-tooltip" style={{ pointerEvents: "none" }}>
          {JSON.stringify(tooltipData, null, 2)}
        </pre>
      )}

      <Handle type="source" position={Position.Bottom} style={sourceHandleStyle} />
    </div>
  );
};

export default LineageNode;