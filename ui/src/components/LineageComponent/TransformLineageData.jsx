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
 * Data Transformers for Lineage View Graphs
 * Automatically detects and normalizes raw MLMD backend data shapes into consistent graph structures.
 * 
 * This module exports `transformLineageData`, which handles two distinct visualization data flows:
 * 1. Flat Lineage Format: Processes a raw flat array of related artifact dependencies into a network graph.
 *    - Uses string-matching rules to classify IDs into Metrics, Models, Datasets, or Executions.
 * 2. Hierarchical Stage Format: Processes nested stage pipeline wrappers down into individual executions.
 *    - Unrolls hierarchical parent-child schemas recursively (`addExecutionChildren`) into discrete layout node sets.
 * 
 * returns {Object} A unified graph schema object containing flat `nodes` and directional edge `links`.
 */

/**
 * Infers the UI type for a node identifier using case-insensitive keyword matching.
 *
 * @param {string} id Node or artifact identifier to classify.
 * @returns {string} One of the lineage node types used by the graph renderer.
 */

const determineType = (id, explicitType) => {
  if (explicitType) return explicitType;
  if (!id) return "Execution";

  const normalized = String(id).toLowerCase();

  if (normalized.startsWith("execution_name_") || normalized.startsWith("execution_")) {
    return "Execution";
  }
  if (normalized.startsWith("artifact_name_") || normalized.startsWith("artifact_")) {
    return "Dataset";
  }
  
  if (normalized.includes("metrics")) return "Metrics";
  if (normalized.includes("model")) return "Model";
  if (
    normalized.includes("train") ||
    normalized.includes("test") ||
    normalized.includes(".xml") ||
    normalized.includes("dataset") ||
    normalized.includes("input") ||
    normalized.includes("output")
  ) {
    return "Dataset";
  }
  return "Execution";
};

const getDisplayName = (id) =>
  String(id).replace(/^(artifact_name_|execution_name_)/, "");

/**
 * Transforms a raw flat array of related artifacts into a deduplicated graph.
 * Parent identifiers that are referenced but not present as items are added as
 * standalone nodes so every generated link has a corresponding node.
 *
 * @param {Array<Array<Object>|Object>} rawJson Flat lineage records, optionally nested one level.
 * @param {string} [nodeType] Optional type override for lineage formats whose records are known to be executions.
 * @returns {{nodes: Array<Object>, links: Array<{source: string, target: string}>}} Graph data.
 */

const transformFlatLineageData = (rawJson, nodeType) => {
  const flatItems = rawJson.flat();
  const originalNodeMap = new Map();

  // Normalize duplicate parent identifiers before building the graph.
  flatItems.forEach((item) => {
    if (!item || !item.id) return;

    const parents = item.parents ? Array.from(new Set(item.parents)).sort() : [];

    if (!originalNodeMap.has(item.id)) {
      originalNodeMap.set(item.id, {
        id: item.id,
        name: getDisplayName(item.id),
        type: determineType(item.id, nodeType),
        parents,
      });
    }

    parents.forEach((parentId) => {
      if (!originalNodeMap.has(parentId)) {
        originalNodeMap.set(parentId, {
          id: parentId,
          name: getDisplayName(parentId),
          type: determineType(parentId, nodeType),
          parents: [],
        });
      }
    });
  });

  const rawLinks = [];
  const edgeSet = new Set();
  const adjacency = new Map();

  // Build unique parent-to-child links and an adjacency map for reduction.
  originalNodeMap.forEach((node) => {
    node.parents.forEach((parentId) => {
      if (parentId !== node.id) {
        const edgeKey = `${parentId}->${node.id}`;
        if (!edgeSet.has(edgeKey)) {
          edgeSet.add(edgeKey);
          rawLinks.push({ source: parentId, target: node.id });
          if (!adjacency.has(parentId)) adjacency.set(parentId, new Set());
          adjacency.get(parentId).add(node.id);
        }
      }
    });
  });

  const reachabilityFrom = new Map();
  /**
   * Finds every node reachable from a starting node for transitive edge removal.
   *
   * @param {string} start Node identifier from which to traverse.
   * @returns {Set<string>} All downstream node identifiers.
   */
  const computeReachable = (start) => {
    if (reachabilityFrom.has(start)) return reachabilityFrom.get(start);

    const visited = new Set();
    const stack = [...(adjacency.get(start) || [])];
    while (stack.length) {
      const current = stack.pop();
      if (visited.has(current)) continue;
      visited.add(current);
      (adjacency.get(current) || []).forEach((next) => {
        if (!visited.has(next)) stack.push(next);
      });
    }
    reachabilityFrom.set(start, visited);
    return visited;
  };

  // Remove indirect links when a direct path already represents the relationship.
  const links = rawLinks.filter(({ source, target }) => {
    const neighbours = adjacency.get(source);
    if (!neighbours || neighbours.size <= 1) return true;

    for (const neighbour of neighbours) {
      if (neighbour !== target && computeReachable(neighbour).has(target)) {
        return false;
      }
    }
    return true;
  });

  return { nodes: Array.from(originalNodeMap.values()), links };
};

/**
 * Flattens hierarchical pipeline data into renderer-friendly nodes and links.
 * Invalid or stage-less input produces an empty graph.
 *
 * @param {Object} rawJson Pipeline data containing stages, executions, and optional children.
 * @returns {{nodes: Array<Object>, links: Array<{source: string, target: string}>}} Graph data.
 */

const transformNestedStageData = (rawJson) => {
  const nodes = [];
  const links = [];

  if (!rawJson?.stages) {
    return { nodes, links };
  }

  const pipelineId = `${rawJson.pipeline || "pipeline"}`;
  nodes.push({ id: pipelineId, name: rawJson.pipeline || "Pipeline", type: "Pipeline" });

  /**
   * Recursively adds nested execution children and their parent-child links.
   *
   * @param {Object} execution Execution object that may contain children.
   * @param {string} executionId Identifier of the parent graph node.
   * @returns {void}
   */
  const addExecutionChildren = (execution, executionId) => {
    if (!Array.isArray(execution.children)) return;

    execution.children.forEach((child) => {
      const childId = child.node_id || child.execution_id || `${executionId}-${child.node_name}`;

      nodes.push({ id: childId, name: child.node_name || child.execution_type || "Node", type: "Node" });
      links.push({ source: executionId, target: childId });

      if (Array.isArray(child.children)) {
        addExecutionChildren(child, childId);
      }
    });
  };

  rawJson.stages.forEach((stage) => {
    const stageId = `stage-${stage.stage_id}`;

    nodes.push({ id: stageId, name: stage.stage_name, type: "Stage" });
    links.push({ source: pipelineId, target: stageId });

    if (Array.isArray(stage.executions)) {
      stage.executions.forEach((exec) => {
        const execId = `exec-${exec.execution_id}`;
        const [execName, execUuidLine] = (exec.execution_type || "Execution").split("\n");

        nodes.push({
          id: execId,
          name: execName || "Execution",
          type: "Execution",
          uuid: "",
          fullUuid: exec.full_uuid || execUuidLine || "",
        });
        links.push({ source: stageId, target: execId });
        addExecutionChildren(exec, execId);
      });
    }
  });

  return { nodes, links };
};

/**
 * Normalizes any supported lineage response into the graph schema consumed by the UI.
 * Existing graph-shaped data is returned unchanged; arrays use flat lineage rules,
 * and all other objects are interpreted as hierarchical pipeline data.
 *
 * @param {Object|Array|null|undefined} rawJson Raw lineage response from the backend.
 * @param {{nodeType?: string}} [options] Optional normalization options for a known lineage format.
 * @returns {{nodes: Array<Object>, links: Array<{source: string, target: string}>}} Graph data.
 */

export const TransformLineageData = (rawJson, options = {}) => {
  if (!rawJson) return { nodes: [], links: [] };
  if (rawJson?.nodes && rawJson?.links) return rawJson;
  if (Array.isArray(rawJson)) return transformFlatLineageData(rawJson, options.nodeType);
  return transformNestedStageData(rawJson);
};