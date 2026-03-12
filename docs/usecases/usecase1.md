**Scenario**: A data scientist runs multiple experiments with different hyperparameters (learning rate, tree depth, regularization) and needs to reproduce the best result six weeks later.

**Without CMF**: The best model file exists but the exact data split, preprocessing parameters, and random seed used are lost. Reproducing it requires guesswork.

```python
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load data — but which version? No record exists of how this file was generated.
df = pd.read_parquet("data/train_split.parquet")
X, y = df.drop("label", axis=1), df["label"]

# Parameters hardcoded in the script — never persisted alongside the model
model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X, y)

# Save model — filename carries no provenance information
pickle.dump(model, open("models/rf_v3.pkl", "wb"))

# Accuracy manually noted in a spreadsheet (or simply forgotten)
print("Accuracy:", model.score(X, y))  # 0.974 — but linked to nothing
```

Six weeks later, the problems become clear:

- The spreadsheet records `accuracy=0.974` but not which version of `train_split.parquet` was used.

- `train_split.parquet` may have been silently overwritten by a newer preprocessing run.

- The random seed (`42`) and `n_estimators` (`200`) were never saved next to `rf_v3.pkl`.

- There is no link from the model file back to the Git commit of the training script.

- Re-running the script may produce a slightly different model if the data changed.

**With CMF**:
```python
from cmflib.cmf import Cmf

metawriter = Cmf(filepath="mlmd", pipeline_name="fraud_detection")

context = metawriter.create_context("train")
execution = metawriter.create_execution(
    "RandomForest",
    custom_properties={"learning_rate": 0.01, "n_estimators": 200, "seed": 42}
)
metawriter.log_dataset("data/train_split.parquet", "input")
metawriter.log_model("models/rf_v3.pkl", "output", {"accuracy": 0.974})
```

Every run records dataset hash, parameters, and metrics. Reproduction is a single `cmf metadata pull` + re-run with logged parameters.

---
