# cmflib API Reference

## Cmf class

```python
from cmflib.cmf import Cmf

metawriter = Cmf(
    filepath="mlmd",           # path to SQLite metadata store (relative to project root)
    pipeline_name="name",      # pipeline identifier — same across all stages
    custom_properties={},      # optional pipeline-level properties
    graph=False                # set True to enable Neo4j graph layer
)
```

## Method reference

| Method | Signature | Purpose |
|--------|-----------|---------|
| `create_context` | `(pipeline_stage, custom_properties={})` | Declare a stage type |
| `create_execution` | `(execution_type, custom_properties={}, cmd="")` | Start a run; log hyperparameters |
| `log_dataset` | `(url, event, custom_properties={}, label=None, label_properties={})` | Log dataset artifact |
| `log_model` | `(path, event, model_framework="", model_type="", model_name="")` | Log model artifact |
| `log_metric` | `(metrics_name, custom_properties)` | Log one step's metrics (buffered) |
| `commit_metrics` | `(metrics_name)` | Flush buffered metrics to parquet file |
| `log_execution_metrics` | `(metrics_name, custom_properties)` | Log final stage-level metrics |
| `create_dataslice` | `(name)` → `DataSlice` | Create a data subset tracker |
| `finalize` | `()` | Record Git SHA and close execution |

### `log_dataset` parameters
- `url` — artifact path relative to project root
- `event` — `"input"` or `"output"`
- `custom_properties` — dict of arbitrary metadata (e.g. `{"split": "train", "rows": 5000}`)
- `label` — path to labels file (optional)
- `label_properties` — metadata for the labels file (optional)

### `log_model` parameters
- `path` — model file path relative to project root
- `event` — `"input"` or `"output"`
- `model_framework` — e.g. `"scikit-learn"`, `"pytorch"`, `"tensorflow"`
- `model_type` — e.g. `"RandomForestClassifier"`, `"ResNet50"`
- `model_name` — human-readable identifier, e.g. `"RandomForestClassifier:v1"`

## DataSlice API

```python
dataslice = metawriter.create_dataslice("validation-slice-female")
for sample_id in sample_ids:
    dataslice.add_data(f"data/raw/{sample_id}.json")
dataslice.commit()
```

Use data slices to track subsets of data for fairness and bias analysis across model versions.
