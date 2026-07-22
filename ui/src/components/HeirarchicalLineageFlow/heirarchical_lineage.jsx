import React, { useMemo, useState } from "react";
import ReactFlow, { Controls, Background, MiniMap, MarkerType, useNodes } from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";
import "./index.css";
import LineageNode1 from "./lineagenode";

const nodeTypes = { lineageNode: LineageNode1 };
const nodeWidth = 220; 
const nodeHeight = 80;

// Central color thematic scheme helper matching your MiniMap rules
const getNodeThemeColor = (type) => {
  switch (type) {
    case "Environment": return "#10b981"; // Green
    case "Stage": return "#f59e0b";   // Amber / Orange
    case "Model": return "#f59e0b";   // Alias fallback
    case "Node": return "#ef4444"; // Red
    case "Execution": return "#3b82f6"; // Blue
    default: return "#64748b";        // Gray
  }
};

// MiniMap Node Component 
const CustomMiniMapNode = ({ id, x, y, width, height }) => {
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
        fill={getNodeThemeColor(nodeType)}
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

// MODIFIED: Generates the exact clean layout tree seen in your example image
const transformLineageData = (rawJson) => {
  const nodesMap = new Map();
  const links = [];
  const flatItems = rawJson.flat();

  const determineType = (id) => {
    if (id.toLowerCase().includes("metrics")) return "Metrics";
    if (id.toLowerCase().includes("model")) return "Stage"; 
    if (id.toLowerCase().includes("train") || id.toLowerCase().includes("test") || id.toLowerCase().includes(".xml") || id.toLowerCase().includes("dataset") || id.toLowerCase().includes("input") || id.toLowerCase().includes("output")) return "Dataset";
    return "Execution";
  };

  // Step 1: Parse every element as an independent individual tree node (No Collapsing)
  flatItems.forEach((item) => {
    if (!item || !item.id) return;
    
    // Clean string name labels cleanly
    let cleanName = item.id.split("/").pop().split(":")[0];
    const type = determineType(item.id);

    if (!nodesMap.has(item.id)) {
      nodesMap.set(item.id, {
        id: item.id,
        name: cleanName,
        type: type,
        parents: item.parents || []
      });
    }
  });

  // Step 2: Directly map one-to-one edges to allow separate parallel branching
  const finalizedEdgesSet = new Set();
  nodesMap.forEach((node) => {
    node.parents.forEach((parentId) => {
      if (nodesMap.has(parentId) && parentId !== node.id) {
        const edgeKey = `${parentId}->${node.id}`;
        if (!finalizedEdgesSet.has(edgeKey)) {
          finalizedEdgesSet.add(edgeKey);
          links.push({ source: parentId, target: node.id });
        }
      }
    });
  });

  return { nodes: Array.from(nodesMap.values()), links };
};

// Layout reconfigured for a top-down vertical tree structure with side-by-side spacing
// FIXED LAYOUT ENGINE: Keeps stages horizontal, stacks ONLY execution leaf nodes vertically
// FIXED LAYOUT ENGINE: Removes massive empty horizontal spacing between stages
const getLayoutedElements = (nodes = [], edges = []) => {
  const g = new dagre.graphlib.Graph();
  
  g.setGraph({
    rankdir: "TB",
    ranksep: 100,       // Vertical gap between Environment and Stages
    nodesep: 40,        // MUCH closer horizontal spacing between your Stage blocks
    edgesep: 20,
    marginx: 40,
    marginy: 40
  });
  g.setDefaultEdgeLabel(() => ({}));

  // STEP 1: Only feed non-Execution nodes (Environment & Stages) into Dagre
  nodes.forEach((node) => {
    if (node.data?.type !== "Execution") {
      g.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    }
  });

  // Only feed edges that don't point to an execution node into Dagre
  edges.forEach((edge) => {
    const targetNode = nodes.find((n) => n.id === edge.target);
    if (targetNode && targetNode.data?.type !== "Execution") {
      g.setEdge(edge.source, edge.target, { weight: 10, minlen: 1 });
    }
  });

  // Layout the main horizontal backbone (Environment -> Stages)
  dagre.layout(g);

  // STEP 2: Group the execution leaves manually by their stage parent
  const parentToExecutionLeavesMap = {};
  nodes.forEach((node) => {
    if (node.data?.type === "Execution") {
      const parentEdge = edges.find((e) => e.target === node.id);
      if (parentEdge) {
        const pId = parentEdge.source;
        if (!parentToExecutionLeavesMap[pId]) parentToExecutionLeavesMap[pId] = [];
        parentToExecutionLeavesMap[pId].push(node.id);
      }
    }
  });

  // STEP 3: Assign positions to all elements
  return nodes?.map((node) => {
    // Default top-down connection routing
    node.targetPosition = 'top';
    node.sourcePosition = 'bottom';

    if (node.data?.type !== "Execution") {
      // Use the compact positions generated by Dagre for main stages
      const pos = g.node(node.id) || { x: 0, y: 0 };
      node.position = {
        x: pos.x - nodeWidth / 2,
        y: pos.y - nodeHeight / 2,
      };
    } else {
      // Calculate clean, compact vertical positions for Execution nodes
      const parentEdge = edges.find((e) => e.target === node.id);
      if (parentEdge) {
        const parentId = parentEdge.source;
        const parentPos = g.node(parentId) || { x: 0, y: 0 };
        const siblings = parentToExecutionLeavesMap[parentId] || [];
        const siblingIndex = siblings.indexOf(node.id);

        node.position = {
          x: parentPos.x - nodeWidth / 2,
          // Increased gap: was +20, now +40 for clearer separation between stacked nodes
          y: (parentPos.y + nodeHeight / 2) + 60 + (siblingIndex * (nodeHeight + 40)),
        };
      }
    }
    return node;
  });
};

const Hierarchical_LineageFlow = ({ data }) => {
  const proOptions = { hideAttribution: true };
  const { nodes, edges } = useMemo(() => {
    if (!data || data.length === 0) return { nodes: [], edges: [] };

    const formattedData = Array?.isArray(data) && !data?.nodes ? transformLineageData(data) : data;

    const rfNodes = formattedData?.nodes?.map((node) => ({
      id: node.id,
      type: "lineageNode",
      position: { x: 0, y: 0 },
      data: { 
        ...node,
      }, 
    }));

    const rfEdges = (formattedData?.links ?? formattedData?.edges ??[]).map((link, index) => ({
      id: `edge-${index}`,
      source: link.source,
      target: link.target,
      type: "step", 
      markerEnd: { 
        type: MarkerType.Arrow, 
        color: "#b1b1b7"
      },
      style: {
        stroke: "#b1b1b7",
        strokeWidth: 1.5,
      }
    }));

    // Layout uses the FULL edge list so every execution sibling gets
    // correctly positioned in its vertical stack
    const layoutedNodes = getLayoutedElements(rfNodes, rfEdges);

    // Only AFTER layout, filter which edges are actually rendered.
    // Keep just the first Stage -> Execution edge per stage (to anchor
    // the stack visually) and drop the rest, so no connecting line
    // appears between stacked execution boxes.
    const seenExecutionEdgeForSource = new Set();
    const renderEdges = rfEdges.filter((edge) => {
      const targetNode = layoutedNodes.find((n) => n.id === edge.target);
      if (targetNode?.data?.type === "Execution") {
        if (seenExecutionEdgeForSource.has(edge.source)) {
          return false;
        }
        seenExecutionEdgeForSource.add(edge.source);
        return true;
      }
      return true;
    });

    return {
      nodes: layoutedNodes,
      edges: renderEdges,
    };
  }, [data]);

  return (
    <div style={{ width: "100%", height: "85vh", position: "relative" }}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        nodeTypes={nodeTypes} 
        fitView                        
        fitViewOptions={{ padding: 0.15, includeHiddenNodes: true }} // Adjusted padding for cleaner fitting on vertical trees
        defaultViewport={{x: 0, y: 0, zoom:1}}
        minZoom={0.2}
        maxZoom={2}
        proOptions={proOptions}
      >
        <MiniMap 
          position="bottom-right" 
          nodeComponent={CustomMiniMapNode} 
          maskColor="rgba(241, 245, 249, 0.4)"
          style={{
            backgroundColor: "#f8fafc",
            border: "1px solid #cbd5e1",
            borderRadius: "8px",
            width: 300, 
            height: 160,
            position: "fixed"
          }}
          zoomable
          pannable
        />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

export default Hierarchical_LineageFlow;