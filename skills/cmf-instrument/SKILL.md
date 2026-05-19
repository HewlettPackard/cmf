---
name: cmf-instrument
description: >
  Use when adding CMF metadata tracking to existing Python ML pipeline code, or writing
  new CMF-instrumented pipeline stages from scratch. Covers importing cmflib, initializing
  Cmf(), creating contexts and executions, logging datasets, models, metrics, and calling
  finalize(). Includes ready-to-use code templates for common ML pipeline patterns.
version: 1.0.0
---

Instrument the user's Python ML code with CMF metadata tracking. Identify the pipeline stages in their code and add the correct CMF calls to each one.

## How CMF instrumentation works

Every pipeline stage follows the same four-step pattern:

```
1. Cmf(...)              → connect to the metadata store
2. create_context(...)   → declare the stage type
3. create_execution(...) → start this particular run (log hyperparameters here)
4. log_dataset / log_model / log_metric  → log inputs and outputs
5. finalize()            → commit code version and close the execution
```

## Step 1 — Import and initialize

```python
from cmflib.cmf import Cmf

metawriter = Cmf(
    filepath="mlmd",                  # local SQLite metadata store
    pipeline_name="my_pipeline",      # must be the same across all stages
    graph=False                       # set True if Neo4j graph layer is configured
)
```

- Use the **same `pipeline_name`** in every stage of the pipeline.
- `filepath` is relative to the project root; `"mlmd"` is the conventional name.
- Add `graph=True` only after running `cmf init` with `--neo4j-*` flags.

## Step 2 — Create context (stage type)

```python
context = metawriter.create_context(
    pipeline_stage="Train",           # stage name — use the same name every run
    custom_properties={               # optional stage-level metadata
        "framework": "scikit-learn",
        "task": "classification"
    }
)
```

Contexts group all executions of the same stage. The `pipeline_stage` name should be consistent across runs (e.g., always `"Train"`, not `"train_v2"`, `"Train_new"`, etc.).

## Step 3 — Create execution (one run)

```python
execution = metawriter.create_execution(
    execution_type="Train",           # usually matches pipeline_stage
    custom_properties={               # hyperparameters and run-specific settings
        "learning_rate": 0.01,
        "n_estimators": 100,
        "seed": 42
    }
)
```

Hyperparameters, random seeds, and any run-specific parameters go in `custom_properties`. CMF guarantees unique execution names automatically.

## Step 4 — Log artifacts

### Datasets

```python
# Input dataset
metawriter.log_dataset(
    "data/train.csv",                 # path relative to project root
    "input",                          # "input" or "output"
    custom_properties={"split": "train", "rows": 10000}
)

# Output dataset
metawriter.log_dataset(
    "data/processed/train.pkl",
    "output",
    custom_properties={"format": "pickle"}
)
```

To log a dataset with its labels file:

```python
metawriter.log_dataset(
    "data/raw.csv",
    "input",
    label="data/labels.csv",
    label_properties={"annotator": "team-a"}
)
```

### Models

```python
# Saving a model (output)
metawriter.log_model(
    path="models/rf.pkl",
    event="output",
    model_framework="scikit-learn",
    model_type="RandomForestClassifier",
    model_name="RandomForestClassifier:v1"
)

# Loading a model (input)
metawriter.log_model(
    path="models/rf.pkl",
    event="input"
)
```

### Per-step metrics (training loop)

```python
for epoch in range(num_epochs):
    loss = train_one_epoch(...)
    metawriter.log_metric("training_metrics", {"loss": loss, "epoch": epoch})

metawriter.commit_metrics("training_metrics")  # write the parquet file and commit
```

### Final / stage metrics

```python
metawriter.log_execution_metrics(
    "eval_metrics",
    {"accuracy": 0.94, "roc_auc": 0.97, "avg_precision": 0.91}
)
```

## Step 5 — Finalize

```python
metawriter.finalize()   # commits code version to Git; call once per stage script
```

Always call `finalize()` at the end of each stage script. It records the Git commit SHA and closes the execution.

## Full stage templates

### Data preparation stage

```python
from cmflib.cmf import Cmf

def prepare(input_path: str, output_dir: str, params: dict) -> None:
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Prepare")
    metawriter.create_execution(execution_type="Prepare", custom_properties=params)

    metawriter.log_dataset(input_path, "input")

    # ... your data processing logic here ...

    metawriter.log_dataset(f"{output_dir}/train.pkl", "output")
    metawriter.log_dataset(f"{output_dir}/test.pkl", "output")
    metawriter.finalize()
```

### Training stage

```python
from cmflib.cmf import Cmf

def train(train_path: str, model_path: str, params: dict) -> None:
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Train")
    metawriter.create_execution(execution_type="Train", custom_properties=params)

    metawriter.log_dataset(train_path, "input")

    # ... your training logic here ...
    model = fit_model(train_path, params)

    for i, loss in enumerate(training_losses):
        metawriter.log_metric("train_metrics", {"loss": loss, "step": i})
    metawriter.commit_metrics("train_metrics")

    save_model(model, model_path)
    metawriter.log_model(
        path=model_path,
        event="output",
        model_framework="scikit-learn",
        model_type="RandomForestClassifier",
        model_name="RandomForestClassifier:default"
    )
    metawriter.finalize()
```

### Evaluation stage

```python
from cmflib.cmf import Cmf

def evaluate(model_path: str, test_path: str, params: dict) -> None:
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Evaluate")
    metawriter.create_execution(execution_type="Evaluate", custom_properties=params)

    metawriter.log_model(path=model_path, event="input")
    metawriter.log_dataset(test_path, "input")

    # ... your evaluation logic here ...
    accuracy, roc_auc = run_evaluation(model_path, test_path)

    metawriter.log_execution_metrics("eval_metrics", {
        "accuracy": accuracy,
        "roc_auc": roc_auc
    })
    metawriter.finalize()
```

## Checklist for instrumenting an existing file

When adding CMF to an existing pipeline script, work through this checklist:

- [ ] Add `from cmflib.cmf import Cmf` at the top
- [ ] Create `metawriter = Cmf(filepath="mlmd", pipeline_name="<pipeline>")` before any logging
- [ ] Call `create_context(pipeline_stage="<StageName>")` — same name every run
- [ ] Call `create_execution(execution_type="<type>", custom_properties=<params_dict>)` — put hyperparameters here
- [ ] Log every significant input file with `log_dataset(..., "input")`
- [ ] Log every significant output file with `log_dataset(..., "output")` or `log_model(..., event="output")`
- [ ] Log per-step metrics inside the training loop, then call `commit_metrics()`
- [ ] Log final stage metrics with `log_execution_metrics()`
- [ ] Call `finalize()` at the end of the stage

## Data slice tracking (bias analysis)

```python
import random

dataslice = metawriter.create_dataslice("validation-slice-female")
for sample_id in random.sample(female_sample_ids, 200):
    dataslice.add_data(f"data/raw/{sample_id}.json")
dataslice.commit()
```

Use data slices to track subsets of data for fairness and bias analysis.

## Quick reference

| Method | Signature | Purpose |
|--------|-----------|---------|
| `Cmf()` | `Cmf(filepath, pipeline_name, graph=False)` | Connect to metadata store |
| `create_context()` | `create_context(pipeline_stage, custom_properties={})` | Declare stage type |
| `create_execution()` | `create_execution(execution_type, custom_properties={}, cmd="")` | Start a run |
| `log_dataset()` | `log_dataset(url, event, custom_properties={}, label=None)` | Log dataset artifact |
| `log_model()` | `log_model(path, event, model_framework="", model_type="", model_name="")` | Log model artifact |
| `log_metric()` | `log_metric(metrics_name, custom_properties)` | Log per-step metric |
| `commit_metrics()` | `commit_metrics(metrics_name)` | Finalize step metrics |
| `log_execution_metrics()` | `log_execution_metrics(metrics_name, custom_properties)` | Log final stage metrics |
| `create_dataslice()` | `create_dataslice(name)` | Create a data subset tracker |
| `finalize()` | `finalize()` | Commit code version and close execution |

## Common mistakes

- **Wrong `pipeline_name`** across stages: stages won't be grouped into the same pipeline. Use the exact same string.
- **Calling `create_context` with a different name each run**: this creates a new stage type every run. Keep the `pipeline_stage` name stable.
- **Logging absolute paths**: use paths relative to the project root so CMF can identify the same artifact across environments.
- **Forgetting `finalize()`**: the Git commit SHA won't be recorded, breaking reproducibility tracking.
- **Logging metrics without `commit_metrics()`**: step metrics are buffered; they won't be persisted without a commit call.

## Further reading

- `docs/cmflib/index.md` — Full API reference with diagrams
- `examples/example-get-started/src/` — Complete 4-stage pipeline example (parse, featurize, train, test)
- `docs/examples/getting_started.md` — Getting started tutorial
