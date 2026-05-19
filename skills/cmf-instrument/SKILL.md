---
name: cmf-instrument
description: >
  Use when adding CMF metadata tracking to existing Python ML pipeline code, or writing
  new CMF-instrumented pipeline stages from scratch. Covers the Cmf() API: create_context,
  create_execution, log_dataset, log_model, log_metric, commit_metrics, log_execution_metrics,
  and finalize(). Includes copy-paste templates for common ML pipeline stages.
version: 1.0.0
---

Add CMF tracking to the user's Python pipeline. Identify each stage and apply the five-step pattern below.

## The five-step pattern (every stage)

```python
from cmflib.cmf import Cmf

metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")  # 1. connect
metawriter.create_context(pipeline_stage="Train")               # 2. stage type
metawriter.create_execution(                                     # 3. this run
    execution_type="Train",
    custom_properties={"learning_rate": 0.01, "seed": 42}       #    ← hyperparameters go here
)
metawriter.log_dataset("data/train.csv", "input")               # 4. log artifacts
metawriter.log_model("models/rf.pkl", event="output",           #
    model_framework="scikit-learn",
    model_type="RandomForestClassifier",
    model_name="RandomForestClassifier:v1"
)
metawriter.finalize()                                            # 5. record git SHA
```

Rules:
- Use the **same `pipeline_name`** in every stage of the pipeline
- Keep `pipeline_stage` name stable across runs (don't add version suffixes)
- All artifact paths must be **relative to the project root**
- Call `finalize()` once per stage script

## Logging datasets

```python
metawriter.log_dataset("data/raw.csv", "input")
metawriter.log_dataset("data/processed/train.pkl", "output",
    custom_properties={"format": "pickle", "rows": 10000})

# With labels file
metawriter.log_dataset("data/raw.csv", "input",
    label="data/labels.csv", label_properties={"annotator": "team-a"})
```

## Logging models

```python
# Output (saving)
metawriter.log_model("models/rf.pkl", event="output",
    model_framework="scikit-learn",
    model_type="RandomForestClassifier",
    model_name="RandomForestClassifier:v1")

# Input (loading)
metawriter.log_model("models/rf.pkl", event="input")
```

## Logging metrics

```python
# Per-step metrics (inside training loop)
for epoch in range(num_epochs):
    metawriter.log_metric("train_metrics", {"loss": loss, "epoch": epoch})
metawriter.commit_metrics("train_metrics")   # ← must call to persist

# Final stage metrics
metawriter.log_execution_metrics("eval_metrics",
    {"accuracy": 0.94, "roc_auc": 0.97})
```

## Stage templates

### Data preparation
```python
def prepare(input_path, output_dir, params):
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Prepare")
    metawriter.create_execution(execution_type="Prepare", custom_properties=params)

    metawriter.log_dataset(input_path, "input")
    # ... your processing logic ...
    metawriter.log_dataset(f"{output_dir}/train.pkl", "output")
    metawriter.log_dataset(f"{output_dir}/test.pkl", "output")
    metawriter.finalize()
```

### Training
```python
def train(train_path, model_path, params):
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Train")
    metawriter.create_execution(execution_type="Train", custom_properties=params)

    metawriter.log_dataset(train_path, "input")
    model = fit_model(train_path, params)

    for i, loss in enumerate(training_losses):
        metawriter.log_metric("train_metrics", {"loss": loss, "step": i})
    metawriter.commit_metrics("train_metrics")

    save_model(model, model_path)
    metawriter.log_model(model_path, event="output",
        model_framework="scikit-learn",
        model_type="RandomForestClassifier",
        model_name="RandomForestClassifier:default")
    metawriter.finalize()
```

### Evaluation
```python
def evaluate(model_path, test_path, params):
    metawriter = Cmf(filepath="mlmd", pipeline_name="my_pipeline")
    metawriter.create_context(pipeline_stage="Evaluate")
    metawriter.create_execution(execution_type="Evaluate", custom_properties=params)

    metawriter.log_model(model_path, event="input")
    metawriter.log_dataset(test_path, "input")
    accuracy, roc_auc = run_evaluation(model_path, test_path)
    metawriter.log_execution_metrics("eval_metrics",
        {"accuracy": accuracy, "roc_auc": roc_auc})
    metawriter.finalize()
```

## Instrumentation checklist

- [ ] `from cmflib.cmf import Cmf` added at top
- [ ] `Cmf(filepath="mlmd", pipeline_name="<pipeline>")` — same name every stage
- [ ] `create_context(pipeline_stage="<StageName>")` — stable name
- [ ] `create_execution(...)` — hyperparameters in `custom_properties`
- [ ] Every significant input logged with `"input"`, every output with `"output"`
- [ ] `commit_metrics()` called after every `log_metric()` loop
- [ ] `finalize()` at the end

See [references/api-reference.md](references/api-reference.md) for the full method signature table and data slice API.

---

**Docs:** [cmflib API](https://hewlettpackard.github.io/cmf/cmflib/) · [Cmf class reference](https://hewlettpackard.github.io/cmf/api/public/cmf/) · [Getting Started tutorial](https://hewlettpackard.github.io/cmf/examples/getting_started/)
