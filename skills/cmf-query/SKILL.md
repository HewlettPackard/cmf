---
name: cmf-query
description: >
  Use when querying CMF metadata programmatically — listing pipelines, stages, and
  executions; retrieving artifact lineage; exploring relationships between datasets,
  models, and executions; or exporting metadata for analysis. Uses the CmfQuery
  Python API and the CMF CLI listing commands.
version: 1.0.0
---

Help the user query CMF metadata using the `CmfQuery` Python API or CLI commands. Identify what they want to find (pipeline overview, artifact lineage, execution history, specific artifacts) and write the correct query.

## Two ways to query CMF

| Method | When to use |
|--------|------------|
| `CmfQuery` Python API | Custom scripts, analysis notebooks, automation |
| CMF CLI (`cmf pipeline/execution/artifact list`) | Quick inspection from the terminal |

## CmfQuery Python API

### Initialize

```python
from cmflib.cmfquery import CmfQuery

# Point to the local mlmd file (or a downloaded one)
query = CmfQuery(filepath="mlmd")
```

### List pipelines

```python
pipelines = query.get_pipeline_names()
print(pipelines)
# ['my_pipeline', 'experiment_v2']
```

### List stages in a pipeline

```python
stages = query.get_pipeline_stages("my_pipeline")
print(stages)
# ['Prepare', 'Train', 'Evaluate']
```

### List executions in a stage

```python
import pandas as pd

executions: pd.DataFrame = query.get_all_executions_in_stage("Train")
print(executions[["name", "id", "learning_rate", "n_estimators"]])
```

Returns a `pandas.DataFrame` with one row per execution and columns for all logged custom properties.

### Get all executions for a pipeline

```python
executions = query.get_all_executions_in_pipeline("my_pipeline")
```

### Get a specific artifact

```python
artifact = query.get_artifact("data/train.csv")
print(artifact)
```

### Get all artifacts in a pipeline

```python
datasets = query.get_all_artifacts_for_pipeline("my_pipeline")
print(datasets)
```

### Get artifact lineage — one hop upstream

```python
# What artifacts fed INTO this artifact?
parents = query.get_one_hop_parent_artifacts("models/rf.pkl")
```

### Get artifact lineage — one hop downstream

```python
# What artifacts were produced FROM this artifact?
children = query.get_one_hop_child_artifacts("data/train.csv")
```

### Get parent executions of an artifact

```python
# Which executions produced this artifact?
parent_executions = query.get_one_hop_parent_executions("models/rf.pkl")
```

### Get all executions for a pipeline (DataFrame)

```python
all_executions = query.get_all_executions_in_pipeline("my_pipeline")
# Filter to a specific stage
train_runs = all_executions[all_executions["type"] == "Train"]
```

## Common query patterns

### Compare hyperparameters across training runs

```python
from cmflib.cmfquery import CmfQuery
import pandas as pd

query = CmfQuery(filepath="mlmd")
runs = query.get_all_executions_in_stage("Train")

# Show learning_rate and accuracy for each run
comparison = runs[["name", "learning_rate", "n_estimators"]].copy()
print(comparison.sort_values("learning_rate"))
```

### Trace a model's full data lineage

```python
from cmflib.cmfquery import CmfQuery

query = CmfQuery(filepath="mlmd")

model_path = "models/rf.pkl"
print(f"Parents of {model_path}:")
parents = query.get_one_hop_parent_artifacts(model_path)
print(parents)

for parent in parents["name"].tolist():
    print(f"  Parents of {parent}:")
    grandparents = query.get_one_hop_parent_artifacts(parent)
    print(grandparents)
```

### Find all models produced by a pipeline

```python
from cmflib.cmfquery import CmfQuery

query = CmfQuery(filepath="mlmd")
artifacts = query.get_all_artifacts_for_pipeline("my_pipeline")
models = artifacts[artifacts["type"] == "Model"]
print(models[["name", "id", "uri"]])
```

### List all datasets consumed by a stage

```python
from cmflib.cmfquery import CmfQuery

query = CmfQuery(filepath="mlmd")
executions = query.get_all_executions_in_stage("Train")

for exec_id in executions["id"]:
    inputs = query.get_all_artifacts_for_execution(exec_id, event="input")
    print(f"Execution {exec_id} inputs:", inputs["name"].tolist())
```

## CLI quick inspection

```bash
# List all pipelines in the local mlmd
cmf pipeline list

# List executions for a pipeline
cmf execution list -p my_pipeline

# List artifacts for a pipeline
cmf artifact list -p my_pipeline
```

## CmfQuery quick reference

| Method | Returns | Purpose |
|--------|---------|---------|
| `get_pipeline_names()` | `list[str]` | All pipeline names |
| `get_pipeline_stages(pipeline)` | `list[str]` | Stage names in a pipeline |
| `get_all_executions_in_stage(stage)` | `DataFrame` | All executions for a stage |
| `get_all_executions_in_pipeline(pipeline)` | `DataFrame` | All executions in a pipeline |
| `get_artifact(name)` | `dict` | Single artifact by name/path |
| `get_all_artifacts_for_pipeline(pipeline)` | `DataFrame` | All artifacts in a pipeline |
| `get_all_artifacts_for_execution(exec_id, event)` | `DataFrame` | Artifacts for one execution |
| `get_one_hop_parent_artifacts(artifact)` | `DataFrame` | Direct parents of an artifact |
| `get_one_hop_child_artifacts(artifact)` | `DataFrame` | Direct children of an artifact |
| `get_one_hop_parent_executions(artifact)` | `DataFrame` | Executions that produced an artifact |

## Troubleshooting

- **`mlmd file not found`**: Pass the correct path to `CmfQuery(filepath=...)`. Run `cmf metadata pull -p <name>` first if querying a teammate's runs.
- **Empty DataFrame returned**: The pipeline name or stage name might not match what was logged. Check with `query.get_pipeline_names()` and `query.get_pipeline_stages(pipeline)`.
- **`AttributeError` on query result**: Query methods return `pandas.DataFrame`; use `.tolist()`, `.itertuples()`, or standard DataFrame operations to iterate.

## Further reading

- `docs/api/public/cmfquery.md` — Complete CmfQuery API reference
- `docs/ui/lineage.md` — Web UI lineage graph visualization
- `docs/ui/executions.md` — Web UI execution browser
- `docs/mcp/index.md` — Natural language queries via AI assistant + MCP server
