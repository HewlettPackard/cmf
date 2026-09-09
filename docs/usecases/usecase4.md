**Scenario**: A team runs 200 training experiments but only changes hyperparameters, not the input data. Without tracking, they may save 200 copies of the same dataset.

**Without CMF**: Each experiment script saves its own copy of the processed dataset to a versioned folder (e.g., `data_run_001/`, `data_run_002/`). After 200 runs, terabytes of redundant data accumulate on shared storage. There is no programmatic way to determine which dataset files are identical, and deleting files risks breaking references in older notebooks.

```python
import os, shutil, pickle
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

hyperparams = [
    {"n_estimators": 100, "max_depth": 3, "lr": 0.05},
    {"n_estimators": 200, "max_depth": 4, "lr": 0.10},
    # ... 198 more combinations
]

for run_id, params in enumerate(hyperparams):
    run_dir = f"data_run_{run_id:03d}"
    os.makedirs(run_dir, exist_ok=True)

    # ❌ Full dataset copied for every run — even though only params change
    shutil.copy("data/processed_features.parquet", f"{run_dir}/features.parquet")

    df = pd.read_parquet(f"{run_dir}/features.parquet")
    X, y = df.drop("label", axis=1), df["label"]

    model = GradientBoostingClassifier(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        learning_rate=params["lr"]
    )
    model.fit(X, y)

    # Model saved, but no link to which data file or params produced it
    pickle.dump(model, open(f"{run_dir}/model.pkl", "wb"))
    print(f"Run {run_id}: accuracy={model.score(X, y):.4f}")
    # Result printed only — never queryable later

# After 200 runs: 200 identical copies of processed_features.parquet on disk.
# Deleting data_run_042/ to free space? Hope nothing references it.
# Finding the best run? Manually scan 200 print outputs or re-run everything.
```

**With CMF**: Artifacts are identified by **content hash**. If the dataset hasn't changed, it is stored once and referenced by hash across all 200 executions. Storage overhead is reduced to only the truly unique artifacts.

```python
from cmflib.cmf import Cmf
from cmflib.cmfquery import CmfQuery

hyperparams = [
    {"n_estimators": 100, "max_depth": 3, "lr": 0.05},
    {"n_estimators": 200, "max_depth": 4, "lr": 0.10},
    # ... 198 more combinations
]

for run_id, params in enumerate(hyperparams):
    metawriter = Cmf(filepath="mlmd", pipeline_name="hyperparameter_search")
    ctx  = metawriter.create_context("train")
    exec = metawriter.create_execution(
        "GradientBoosting",
        custom_properties={
            "run_id": run_id,
            "n_estimators": params["n_estimators"],
            "max_depth": params["max_depth"],
            "lr": params["lr"]
        }
    )

    # ✅ Same file path every run — CMF detects content hash is unchanged
    # and records a reference; no duplicate is stored on the DVC backend
    metawriter.log_dataset("data/processed_features.parquet", "input")

    import pandas as pd
    from sklearn.ensemble import GradientBoostingClassifier
    df = pd.read_parquet("data/processed_features.parquet")
    X, y = df.drop("label", axis=1), df["label"]
    model = GradientBoostingClassifier(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        learning_rate=params["lr"]
    )
    model.fit(X, y)
    accuracy = model.score(X, y)

    import pickle
    model_path = f"models/gb_run_{run_id:03d}.pkl"
    pickle.dump(model, open(model_path, "wb"))

    # ✅ Accuracy stored in metadata — queryable later without re-running
    metawriter.log_model(model_path, "output", {"accuracy": round(accuracy, 4)})

# Find the best run instantly — no re-running, no log scanning
q = CmfQuery("mlmd")
execs = q.get_all_executions_in_pipeline("hyperparameter_search")
best  = execs.loc[execs["accuracy"].idxmax()]
print(f"Best run {int(best['run_id'])}: "
      f"n_estimators={int(best['n_estimators'])}, "
      f"max_depth={int(best['max_depth'])}, "
      f"lr={best['lr']}, "
      f"accuracy={best['accuracy']:.4f}")

# Storage result: processed_features.parquet stored ONCE on DVC backend.
# All 200 executions point to the same content hash — zero duplication.
```
