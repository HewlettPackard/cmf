export const transformNestedStageData = (rawJson) => {
  const nodes = [];
  const links = [];

  if (!rawJson?.stages) {
    return { nodes, links };
  }

  const envId = `env-${rawJson.environment || "env"}`;

  nodes.push({
    id: envId,
    name: rawJson.environment || "Environment",
    type: "Environment",
  });

  const addExecutionChildren = (execution, executionId) => {
    if (!Array.isArray(execution.children)) return;

    execution.children.forEach((child) => {
      const childId =
        child.node_id ||
        child.execution_id ||
        `${executionId}-${child.node_name}`;

      nodes.push({
        id: childId,
        name:
          child.node_name ||
          child.execution_type ||
          "Node",
        type: "Node",
      });

      links.push({
        source: executionId,
        target: childId,
      });

      // Recursive support
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

    if (Array.isArray(stage.executions)) {
      stage.executions.forEach((exec) => {
        const execId = `exec-${exec.execution_id}`;

        nodes.push({
          id: execId,
          name: exec.execution_type,
          type: "Execution",
        });

        links.push({
          source: stageId,
          target: execId,
        });

        // ADD CHILD NODES HERE
        addExecutionChildren(exec, execId);
      });
    }
  });

  return { nodes, links };
};