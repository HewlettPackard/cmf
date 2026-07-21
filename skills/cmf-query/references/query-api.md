# CmfQuery API Reference

```python
from cmflib.cmfquery import CmfQuery
query = CmfQuery(filepath="mlmd")
```

## Method reference

| Method | Returns | Purpose |
|--------|---------|---------|
| `get_pipeline_names()` | `list[str]` | All pipeline names |
| `get_pipeline_stages(pipeline)` | `list[str]` | Stage names in a pipeline |
| `get_all_executions_in_stage(stage)` | `DataFrame` | All executions for a stage, with custom_properties as columns |
| `get_all_executions_in_pipeline(pipeline)` | `DataFrame` | All executions in a pipeline |
| `get_artifact(name)` | `dict` | Single artifact by name/path |
| `get_all_artifacts_for_pipeline(pipeline)` | `DataFrame` | All artifacts in a pipeline |
| `get_all_artifacts_for_execution(exec_id, event)` | `DataFrame` | Artifacts for one execution |
| `get_one_hop_parent_artifacts(artifact)` | `DataFrame` | Direct parents of an artifact |
| `get_one_hop_child_artifacts(artifact)` | `DataFrame` | Direct children of an artifact |
| `get_one_hop_parent_executions(artifact)` | `DataFrame` | Executions that produced an artifact |

All DataFrame-returning methods return `pandas.DataFrame`. Use standard DataFrame operations (`.tolist()`, filtering, `.sort_values()`) to process results.
