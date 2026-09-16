
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
 * Shared building blocks used by both lineage graph renderers
 * (CommonLineageComponent and HierarchicalLineageFlow):
 *  - a generic MiniMap node renderer with a pluggable color mapping
 *  - a generic ReactFlow canvas wrapper (MiniMap + Controls + Background)
 *  - helpers to convert transformed lineage data into React Flow nodes/edges
 *
 * Each component keeps its own layout algorithm, node/color palette, and
 * edge styling — only the parts that were byte-for-byte identical (or
 * trivially parameterizable) were moved here.
 */

import React from "react";
import ReactFlow, { Controls, Background, MiniMap, MarkerType, useNodes } from "reactflow";
import "reactflow/dist/style.css";

export const nodeWidth = 220;

const PRO_OPTIONS = { hideAttribution: true };

/**
 * Generic MiniMap node. `colorFn` maps a node's `type` to a background
 * color so each graph can keep its own palette.
 */
export const CustomMiniMapNode = ({ id, x, y, width, height, colorFn }) => {
  const nodes = useNodes();
  const graphNode = nodes.find((n) => n.id === id);
  const nodeType = graphNode?.data?.type || "Node";
  const nodeName = graphNode?.data?.name || "";

  return (
    <g transform={`translate(${x},${y})`}>
      <rect
        width={width}
        height={height}
        rx={8}
        ry={8}
        fill={colorFn(nodeType)}
        stroke="#ffffff"
        strokeWidth={2}
      />
      <text
        x={width / 2}
        y={height / 3 + 4}
        textAnchor="middle"
        fill="#ffffff"
        style={{
          fontSize: "20px",
          fontWeight: "bold",
          fontFamily: "Inter, sans-serif",
          pointerEvents: "none",
        }}
      >
        {nodeType.toUpperCase()}
      </text>
      <text
        x={width / 2}
        y={(2 * height) / 3 + 8}
        textAnchor="middle"
        fill="rgba(255, 255, 255, 0.9)"
        style={{
          fontSize: "16px",
          fontFamily: "Inter, sans-serif",
          pointerEvents: "none",
        }}
      >
        {nodeName.length > 18 ? `${nodeName.substring(0, 16)}...` : nodeName}
      </text>
    </g>
  );
};

/**
 * Converts transformed lineage nodes into React Flow node objects.
 * `type` lets each caller plug in its own custom node renderer key.
 */
export const buildReactFlowNodes = (nodes, type = "lineageNode") =>
  (nodes || []).map((node) => ({
    id: node.id,
    type,
    position: { x: 0, y: 0 },
    data: { ...node },
  }));

/**
 * Converts transformed lineage links into React Flow edge objects.
 * `edgeType`, `markerColor`, `stroke`, and `strokeWidth` let each graph
 * keep its own edge styling.
 */
export const buildReactFlowEdges = (
  links,
  { edgeType = "step", markerColor = "#b1b1b7", stroke = "#b1b1b7", strokeWidth = 1.5 } = {}
) =>
  (links || []).map((link, index) => ({
    id: `edge-${index}`,
    source: link.source,
    target: link.target,
    type: edgeType,
    markerEnd: { type: MarkerType.Arrow, color: markerColor },
    style: { stroke, strokeWidth },
  }));

/**
 * Shared canvas: wraps ReactFlow with the MiniMap/Controls/Background setup
 * used by both lineage graphs. Only the pieces that actually differ between
 * the two graphs (color mapping, fitView options, zoom bounds, viewport,
 * interactivity flags) are exposed as props — everything else (proOptions,
 * MiniMap styling, wrapper div) lives here once.
 */
export const LineageCanvas = ({
  nodes,
  edges,
  nodeTypes,
  colorFn,
  fitViewOptions = { padding: 0.15 },
  defaultViewport,
  minZoom = 0.2,
  maxZoom,
  onlyRenderVisibleElements,
  nodesDraggable,
  nodesConnectable,
  elementsSelectable,
}) => (
  <div style={{ width: "100%", height: "85vh", position: "relative" }}>
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={fitViewOptions}
      defaultViewport={defaultViewport}
      minZoom={minZoom}
      maxZoom={maxZoom}
      proOptions={PRO_OPTIONS}
      onlyRenderVisibleElements={onlyRenderVisibleElements}
      nodesDraggable={nodesDraggable}
      nodesConnectable={nodesConnectable}
      elementsSelectable={elementsSelectable}
    >
      <MiniMap
        position="bottom-right"
        nodeComponent={(props) => <CustomMiniMapNode {...props} colorFn={colorFn} />}
        maskColor="rgba(241, 245, 249, 0.4)"
        style={{
          backgroundColor: "#f8fafc",
          border: "1px solid #cbd5e1",
          borderRadius: "8px",
          width: 300,
          height: 160,
          position: "fixed",
        }}
        zoomable
        pannable
      />
      <Controls />
      <Background />
    </ReactFlow>
  </div>
);