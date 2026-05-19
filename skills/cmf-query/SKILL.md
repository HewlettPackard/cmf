---
name: cmf-query
description: >
  Use when querying CMF metadata programmatically — listing pipelines, stages, executions,
  artifacts; tracing lineage; comparing hyperparameters across runs; or exporting metadata
  for analysis. Uses the CmfQuery Python API or CLI listing commands.
version: 1.0.0
---

Write the query the user needs using `CmfQuery` or the CMF CLI. Identify what they want to find (pipeline overview, lineage, hyperparameter comparison, specific artifacts) and produce the code.

## Initialize

```python
from cmflib.cmfquery import CmfQuery
query = CmfQuery(filepath="mlmd")   # or path to a downloaded mlmd file
```

## Common patterns

### List pipelines and stages
```python
pipelines = query.get_pipeline_names()           # ['my_pipeline', ...]
stages = query.get_pipeline_stages("my_pipeline") # ['Prepare', 'Train', ...]
```

### Executions with hyperparameters
```python
runs = query.get_all_executions_in_stage("Train")
# runs is a pandas DataFrame — one row per run, columns = custom_properties
print(runs[["name", "learning_rate", "n_estimators"]])
```

### Artifact lineage
```python
# What fed INTO this artifact?
parents = query.get_one_hop_parent_artifacts("models/rf.pkl")

# What was produced FROM this artifact?
children = query.get_one_hop_child_artifacts("data/train.csv")

# Which execution produced this artifact?
execs = query.get_one_hop_parent_executions("models/rf.pkl")
```

### Compare runs across a stage
```python
runs = query.get_all_executions_in_stage("Train")
print(runs[["name", "learning_rate", "n_estimators"]].sort_values("learning_rate"))
```

### Walk full lineage (two hops)
```python
model = "models/rf.pkl"
parents = query.get_one_hop_parent_artifacts(model)
for p in parents["name"].tolist():
    grandparents = query.get_one_hop_parent_artifacts(p)
    print(f"{p} ← {grandparents['name'].tolist()}")
```

### All models in a pipeline
```python
artifacts = query.get_all_artifacts_for_pipeline("my_pipeline")
models = artifacts[artifacts["type"] == "Model"]
print(models[["name", "uri"]])
```

## CLI quick inspection

```bash
cmf pipeline list
cmf execution list -p my_pipeline
cmf artifact list  -p my_pipeline
```

See [references/query-api.md](references/query-api.md) for the full CmfQuery method reference.

## Troubleshooting

- **Empty DataFrame** — check pipeline/stage names with `get_pipeline_names()` / `get_pipeline_stages(pipeline)`
- **`mlmd file not found`** — run `cmf metadata pull -p <name>` first if querying a teammate's data
- **`AttributeError`** — query results are `pandas.DataFrame`; use `.tolist()` or standard DataFrame operations

---

**Docs:** [CmfQuery API reference](https://hewlettpackard.github.io/cmf/api/public/cmfquery/) · [Web UI executions](https://hewlettpackard.github.io/cmf/ui/executions/) · [Web UI lineage](https://hewlettpackard.github.io/cmf/ui/lineage/) · [MCP for natural language queries](https://hewlettpackard.github.io/cmf/mcp/)
