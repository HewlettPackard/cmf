// The real transformer used with backend data.

export const transformNestedStageData = (rawJson) => {
// Initialize containers for the final graph structure
  const nodes = [];
  const links = [];

  if (!rawJson?.stages) {
    return { nodes, links };
  }

// Create the root environment node using a unique string ID
  const envId = `${rawJson.environment || "env"}`;

  nodes.push({
    id: envId,
    name: rawJson.environment || "Environment",
    type: "Environment",
  });

//Helper function to recursively traverse and extract nested child execution nodes

  const addExecutionChildren = (execution, executionId) => {
    if (!Array.isArray(execution.children)) return;

    execution.children.forEach((child) => {
      // Determine unique ID using fallback properties to prevent duplicates
      const childId =
        child.node_id ||
        child.execution_id ||
        `${executionId}-${child.node_name}`;

      // Flatten the child node into the main array
      nodes.push({
        id: childId,
        name: child.node_name || child.execution_type || "Node",
        type: "Node",
      });

      // Establish the relationship link from parent to child
      links.push({
        source: executionId,
        target: childId,
      });

      if (Array.isArray(child.children)) {
        addExecutionChildren(child, childId);
      }
    });
  };

  rawJson.stages.forEach((stage) => {
    const stageId = `stage-${stage.stage_id}`;

    nodes.push({
      id: stageId,
      name: stage.stage_name,
      type: "Stage",
    });

    links.push({
      source: envId,
      target: stageId,
    });

    // Process executions belonging to this specific stage
    if (Array.isArray(stage.executions)) {
      stage.executions.forEach((exec) => {
        const execId = `exec-${exec.execution_id}`;

    // Extract display name and optional UUID line from multi-line text string
        const [execName, execUuidLine] = (exec.execution_type || "Execution").split("\n");

        nodes.push({
          id: execId,
          name: execName || "Execution",
          type: "Execution",
          uuid: "",
          fullUuid: exec.full_uuid || execUuidLine || "",
        });

        links.push({
          source: stageId,
          target: execId,
        });

        // Recursively add any deeply nested children belonging to this execution
        addExecutionChildren(exec, execId);
      });
    }
  });

  // Return the complete flat graph payload
  return { nodes, links };
};