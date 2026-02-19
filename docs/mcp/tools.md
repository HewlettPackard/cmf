# Tools Reference

The CMF MCP Server exposes a comprehensive set of tools that enable AI assistants to interact with CMF Server metadata. All tools follow a consistent pattern and return structured JSON responses.

## Tool Categories

Tools are organized into four functional categories:

- **[Pipeline Tools](#pipeline-tools)** - List and explore pipelines
- **[Execution Tools](#execution-tools)** - Retrieve execution details and lineage
- **[Artifact Tools](#artifact-tools)** - Discover and analyze artifacts
- **[Additional Tools](#additional-tools)** - Model cards and specialized queries

## Response Format

All tools return responses as a list of dictionaries, allowing for multi-server queries:

```json
[
  {
    "cmfClient": "http://cmf-server-url:8080",
    "data": [ /* CMF API results */ ]
  }
]
```

When querying multiple CMF Servers, results from each server appear as separate entries in the list.

## Pipeline Tools

### cmf_show_pipelines

Lists all pipelines available in the configured CMF Server(s).

**Description**: Retrieves a comprehensive list of all pipelines in your CMF infrastructure, providing an overview of available ML workflows.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query. If omitted, queries all configured servers. |

**Returns**: List of pipelines with their metadata including pipeline names and properties.

**Example Usage**:

```
Show me all pipelines in CMF
```

```
List pipelines from the production CMF server
```

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": [
      {"name": "Test-env", "id": "1", ...},
      {"name": "training-pipeline", "id": "2", ...}
    ]
  }
]
```

**See Also**: [cmf_show_executions](#cmf_show_executions) to explore executions within a pipeline

---

## Execution Tools

### cmf_show_executions

Retrieves detailed execution information for a specific pipeline.

**Description**: Provides comprehensive details about all executions within a pipeline, including execution parameters, timestamps, and metadata.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline` | string | Yes | Name of the pipeline to query |
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: Detailed execution data including execution UUIDs, names, properties, and relationships.

**Example Usage**:

```
Show me all executions for the Test-env pipeline
```

```
Get execution details for the training-pipeline
```

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": [
      {
        "Execution_uuid": "abc123...",
        "Execution": "train_model",
        "Context_Type": "train",
        ...
      }
    ]
  }
]
```

**See Also**: [cmf_execution_lineage](#cmf_execution_lineage) for lineage analysis

---

### cmf_show_executions_list

Lists execution names for a pipeline (brief list format).

**Description**: Returns a concise list of execution names without full details, useful for quick discovery or when you need just the execution identifiers.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline` | string | Yes | Name of the pipeline to query |
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: Brief list of execution names and UUIDs.

**Example Usage**:

```
List all executions in the Test-env pipeline
```

**When to Use**:
- Quick overview of available executions
- When you need execution names but not full details
- Before calling `cmf_show_executions` for detailed information

**See Also**: [cmf_show_executions](#cmf_show_executions) for full execution details

---

### cmf_execution_lineage

Fetches execution lineage for a specific execution UUID.

**Description**: Retrieves the complete lineage tree showing how an execution relates to other executions, providing a graph of execution dependencies and relationships.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline` | string | Yes | Name of the pipeline containing the execution |
| `selected_uuid` | string | Yes | Execution UUID (only first 4 characters are used) |
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: Execution lineage tree showing parent-child relationships and execution flow.

**Example Usage**:

```
What is the execution lineage for UUID abc123?
```

```
Show me the lineage tree for execution abc1 in Test-env
```

**Important Notes**:
- Only the first 4 characters of the UUID are used for matching
- You should validate the UUID exists before calling this tool
- The response contains a hierarchical tree structure

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": {
      "nodes": [...],
      "edges": [...],
      "hierarchy": {...}
    }
  }
]
```

**See Also**: [cmf_show_executions](#cmf_show_executions) to find valid UUIDs, [Examples: Execution Lineage](examples.md#execution-lineage)

---

## Artifact Tools

### cmf_show_artifact_types

Lists all artifact types available in CMF Server(s).

**Description**: Retrieves the complete list of artifact types tracked in your CMF infrastructure, such as "Dataset", "Model", "Metrics", etc.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: List of artifact type names.

**Example Usage**:

```
What artifact types are available?
```

```
List all artifact types in CMF
```

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": ["Dataset", "Model", "Metrics", "Step_Metrics"]
  }
]
```

**See Also**: [cmf_show_artifacts](#cmf_show_artifacts) to query artifacts of a specific type

---

### cmf_show_artifacts

Retrieves artifacts of a specific type for a given pipeline.

**Description**: Queries artifacts matching a specific type within a pipeline, returning detailed metadata for each artifact.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline` | string | Yes | Name of the pipeline to query |
| `artifact_type` | string | Yes | Type of artifact (e.g., "Model", "Dataset") |
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: List of artifacts with their properties, IDs, and metadata.

**Example Usage**:

```
Show me all Model artifacts in the Test-env pipeline
```

```
Get all Datasets from the training-pipeline
```

**Validation**:
- Use `cmf_show_artifact_types` to verify artifact type exists
- Use `cmf_show_pipelines` to verify pipeline name

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": [
      {
        "id": "42",
        "name": "trained_model.pkl",
        "type": "Model",
        "uri": "s3://bucket/models/trained_model.pkl",
        ...
      }
    ]
  }
]
```

**See Also**: [cmf_show_model_card](#cmf_show_model_card) for detailed model information

---

### cmf_artifact_lineage

Fetches the complete artifact lineage tree for a pipeline.

**Description**: Retrieves the artifact lineage graph showing how artifacts are related through executions, providing a comprehensive view of data flow through your pipeline.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline` | string | Yes | Name of the pipeline to analyze |
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: Artifact lineage tree showing relationships between artifacts and executions.

**Example Usage**:

```
Show me the artifact lineage for Test-env
```

```
What is the artifact flow in the training-pipeline?
```

**Important Notes**:
- Returns a hierarchical structure with nodes and edges
- Shows which executions consume and produce which artifacts
- Useful for understanding data dependencies

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": {
      "nodes": [
        {"id": "artifact-1", "type": "Dataset", ...},
        {"id": "artifact-2", "type": "Model", ...}
      ],
      "edges": [
        {"source": "artifact-1", "target": "execution-1"},
        {"source": "execution-1", "target": "artifact-2"}
      ]
    }
  }
]
```

**See Also**: [cmf_execution_lineage](#cmf_execution_lineage), [Examples: Artifact Lineage](examples.md#artifact-lineage)

---

## Additional Tools

### cmf_show_model_card

Retrieves the model card for a Model artifact.

**Description**: Fetches comprehensive model metadata including training details, input/output artifacts, execution information, and model properties. Returns four distinct sections of model information.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | string | Yes | ID of the model artifact (obtained from `cmf_show_artifacts`) |
| `cmfClient_instances` | List[str] | No | Specific CMF Server URLs to query |

**Returns**: Four sections of model card data:

1. **Model Data** - Basic model properties and metadata
2. **Model Execution** - Training execution details and parameters
3. **Model Input Artifacts** - Datasets and artifacts used for training
4. **Model Output Artifacts** - Generated artifacts and metrics

**Example Usage**:

```
Get the model card for model ID 42
```

```
Show me training details for the model in Test-env
```

**Validation**:
- Use `cmf_show_artifacts` with `artifact_type="Model"` to get valid model IDs
- The `model_id` is returned as the `id` field in artifact listings

**Sample Response**:

```json
[
  {
    "cmfClient": "http://server:8080",
    "data": [
      {
        "Model Data": {
          "id": "42",
          "name": "trained_model.pkl",
          "version": "1.0",
          ...
        },
        "Model Execution": {
          "execution_id": "123",
          "parameters": {...},
          ...
        },
        "Model Input Artifacts": [...],
        "Model Output Artifacts": [...]
      }
    ]
  }
]
```

**See Also**: [cmf_show_artifacts](#cmf_show_artifacts) to find model IDs, [Examples: Model Cards](examples.md#model-cards)

---

## Multi-Server Queries

All tools support the optional `cmfClient_instances` parameter to query specific CMF Servers:

**Query all configured servers** (default):
```python
# Parameter omitted or None
cmf_show_pipelines()
```

**Query specific servers**:
```python
# Provide list of CMF Server URLs
cmf_show_pipelines(cmfClient_instances=["http://server1:8080", "http://server2:8080"])
```

Results are aggregated with each server's response clearly labeled.

## Error Handling

Tools return error information when issues occur:

```json
[
  {
    "cmfClient": "http://server:8080",
    "error": "Pipeline 'invalid-name' not found"
  }
]
```

**Common Errors**:

- **Pipeline not found** - Verify pipeline name with `cmf_show_pipelines`
- **Execution UUID not found** - Verify UUID with `cmf_show_executions`
- **Invalid artifact type** - Check types with `cmf_show_artifact_types`
- **Connection refused** - Ensure CMF Server is running and accessible

## Best Practices

1. **Validate inputs** - Use listing tools before querying specific resources
2. **Handle errors gracefully** - Check for error fields in responses
3. **Query specific servers** - Use `cmfClient_instances` when you know the target server
4. **Start broad, then narrow** - List pipelines → List executions → Get lineage
5. **Check the documentation** - See [Examples](examples.md) for real-world usage patterns

## Next Steps

- **[Examples](examples.md)** - See these tools in action with real-world queries
- **[Configuration](configuration.md)** - Learn about multi-server setup
- **[Quick Start](quickstart.md)** - Get the MCP Server running
