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
 * Renders an interactive hierarchical lineage graph using React Flow.
 * Transforms raw lineage data into nodes and edges, computes a fast
 * top-down rank/barycenter layout, and displays the lineage with custom
 * nodes, edge routing, MiniMap, zoom/pan controls, and fit-to-view support.
 *
 * Shared MiniMap/canvas/node-edge-mapping code lives in ./LineageFlowCommon.
 */

import React, { useMemo } from "react";
import "./index.css";
import lineagenode from "../LineageNode";
import { TransformLineageData } from "../TransformLineageData";
import { LineageCanvas, nodeWidth, buildReactFlowNodes, buildReactFlowEdges} from "../LineageFlowCommon";

// React Flow Configuration Constants
const nodeTypes = { lineageNode: lineagenode };
const nodeHeight = 90;
const RANK_GAP = nodeHeight + 140; // Vertical spacing between graph levels
const FIXED_GAP = nodeWidth + 60;  // Horizontal spacing between adjacent nodes

// Visual mapping for lineage node categories
const TYPE_COLORS = {
  Dataset: "#10b981",
  Model: "#f59e0b",
  Metrics: "#ef4444",
  Execution: "#3b82f6",
};

/**
 * Matches a node ID against naming keywords to resolve its type.
 */
const getBackgroundColor = (type) => TYPE_COLORS[type] || "#64748b";

/**
 * Custom fast Dagre-like layout engine.
 * Computes node coordinates using network in-degrees and Barycenter ordering.
 * 
 * {Array} nodes - React Flow structured node components.
 * {Array} edges - React Flow connection configurations.
 * {Array} Processed node items complete with relative coordinates.
 */
const getLayoutedElements = (nodes, edges) => {
  const nodeIds = nodes.map((n) => n.id);
  const adjacency = new Map();
  const parentsOf = new Map();
  
  nodeIds.forEach((id) => {
    adjacency.set(id, new Set());
    parentsOf.set(id, []);
  });
  
  edges.forEach(({ source, target }) => {
    if (!adjacency.has(source)) adjacency.set(source, new Set());
    adjacency.get(source).add(target);
    if (!parentsOf.has(target)) parentsOf.set(target, []);
    parentsOf.get(target).push(source);
  });

  // Calculate dependency depths (In-degrees)
  const inDegree = new Map();
  nodeIds.forEach((id) => inDegree.set(id, 0));
  edges.forEach(({ target }) => inDegree.set(target, (inDegree.get(target) || 0) + 1));

  // Determine root tracking starting points
  const rank = new Map();
  const queue = [];
  nodeIds.forEach((id) => {
    if ((inDegree.get(id) || 0) === 0) {
      rank.set(id, 0);
      queue.push(id);
    }
  });

  // Breadth-First-Search step calculation to establish hierarchical layers
  const remaining = new Map(inDegree);
  let qi = 0;
  while (qi < queue.length) {
    const u = queue[qi++];
    const uRank = rank.get(u) || 0;
    (adjacency.get(u) || new Set()).forEach((v) => {
      if (!rank.has(v) || rank.get(v) < uRank + 1) rank.set(v, uRank + 1);
      remaining.set(v, remaining.get(v) - 1);
      if (remaining.get(v) === 0) queue.push(v);
    });
  }
  nodeIds.forEach((id) => {
    if (!rank.has(id)) rank.set(id, 0);
  });

  // Assemble horizontal row tracks for the graph
  const rowMap = new Map();
  nodeIds.forEach((id) => {
    const r = rank.get(id);
    if (!rowMap.has(r)) rowMap.set(r, []);
    rowMap.get(r).push(id);
  });
  const sortedRanks = Array.from(rowMap.keys()).sort((a, b) => a - b);

  // Apply Barycenter method sorting to cut down edge crossovers
  const xPosition = new Map();
  sortedRanks.forEach((r) => {
    const rowIds = rowMap.get(r);
    if (r !== 0) {
      rowIds.sort((a, b) => {
        const aParents = parentsOf.get(a) || [];
        const bParents = parentsOf.get(b) || [];
        const aBary = aParents.length
          ? aParents.reduce((sum, p) => sum + (xPosition.get(p) ?? 0), 0) / aParents.length
          : 0;
        const bBary = bParents.length
          ? bParents.reduce((sum, p) => sum + (xPosition.get(p) ?? 0), 0) / bParents.length
          : 0;
        return aBary - bBary;
      });
    }
    // Distribute centers symmetric to the central axis
    const totalWidth = (rowIds.length - 1) * FIXED_GAP;
    const startX = -totalWidth / 2;
    rowIds.forEach((id, index) => xPosition.set(id, startX + index * FIXED_GAP));
  });

  // Format node dimensions and handle connection constraints
  return nodes.map((node) => {
    node.position = {
      x: (xPosition.get(node.id) ?? 0) - nodeWidth / 2,
      y: rank.get(node.id) * RANK_GAP - nodeHeight / 2,
    };
    node.targetPosition = "top";
    node.sourcePosition = "bottom";
    return node;
  });
};

/**
 * Shared wrapper managing lineage tree state conversions and canvas routing.
 */
const CommonLineageComponent = ({ data, lineageType }) => {
  const isArtifactExecutionLineage = lineageType === "Artifact_Execution_Tree";

  // Cache elements array calculations to prevent unnecessary layout computations
  const { nodes, edges } = useMemo(() => {
    if (!data || data.length === 0) return { nodes: [], edges: [] };
    
    // Normalize raw lineage arrays and preserve already-transformed graph data.
    const formattedData = TransformLineageData(data, {
      nodeType: lineageType === "Execution_Tree" ? "Execution" : undefined,
    });

    // Convert datasets into React Flow compliant schema elements
    const rfNodes = buildReactFlowNodes(
      formattedData.nodes.map((node) => ({ ...node, tooltipInteraction: "flat" })),
    );
    const rfEdges = buildReactFlowEdges(formattedData?.links ?? formattedData?.edges ?? [], {
      edgeType: isArtifactExecutionLineage ? "simplebezier" : "step",
    });

    // Run structural positioning calculations
    const laidOutNodes = getLayoutedElements(rfNodes, rfEdges);

    return { nodes: laidOutNodes, edges: rfEdges };
  }, [data, lineageType]);

  return (
    <LineageCanvas
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      colorFn={getBackgroundColor}
      onlyRenderVisibleElements
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
    />
  );
};

export default CommonLineageComponent;