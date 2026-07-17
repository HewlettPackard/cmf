# CMF MCP Tools Reference

The CMF MCP server exposes six tools to AI assistants.

| Tool | Parameters | Returns |
|------|-----------|---------|
| `cmf_show_pipelines` | none | All pipeline names |
| `cmf_show_executions` | `pipeline`, `stage` (optional) | Executions with properties |
| `cmf_execution_lineage` | `execution_id` | Full lineage tree for an execution |
| `cmf_show_artifacts` | `pipeline`, `type` (optional) | Artifacts filtered by type |
| `cmf_artifact_lineage` | `pipeline` | Artifact lineage graph for a pipeline |
| `cmf_show_model_card` | `model_id` | Model metadata, inputs, training details, metrics |

## Example natural language → tool mapping

| User asks | Tool called |
|-----------|------------|
| "What pipelines are in CMF?" | `cmf_show_pipelines` |
| "List executions for Train stage" | `cmf_show_executions` |
| "What's the lineage for execution 42?" | `cmf_execution_lineage(execution_id=42)` |
| "Show datasets in my_pipeline" | `cmf_show_artifacts(pipeline="my_pipeline", type="Dataset")` |
| "Show the model card for model 7" | `cmf_show_model_card(model_id=7)` |

## Multi-server support

Configure up to 4 CMF Servers in `.env`:
```env
CMF_BASE_URL=http://dev-server:80
CMF2_BASE_URL=http://staging-server:80
CMF3_BASE_URL=http://prod-server:80
# CMF4_BASE_URL=http://another-server:80
```
Each server is exposed as a separate context; the assistant can query across environments.
