**Scenario**: A five-stage NLP pipeline where each stage consumes outputs from the previous one.

**Pipeline stages:**

1. `parse` — splits raw corpus into train/test sets

2. `featurize` — generates TF-IDF or embedding features

3. `train` — train a machine learning model

4. `evaluate` — computes precision, recall, F1

**Without CMF**: There is no shared view of how stages connect. Stage outputs are saved as files with no record of which input version they came from. If featurization logic changes, there is no way to tell which downstream models were affected. Re-running a single stage risks using stale inputs from a different run. Cross-stage debugging requires manually correlating file timestamps and notebook outputs.

```python
import json, pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

# ── Stage 1: parse ────────────────────────────────────────────────────────────
# Output written to disk — no record of which raw_corpus.jsonl version was used
with open("raw_corpus.jsonl") as f:
    records = [json.loads(l) for l in f]
train_records = records[:8000]
test_records  = records[8000:]
with open("train_raw.jsonl", "w") as f:
    f.writelines(json.dumps(r) + "\n" for r in train_records)
with open("test_raw.jsonl", "w") as f:
    f.writelines(json.dumps(r) + "\n" for r in test_records)
# Who knows if train_raw.jsonl on disk is from today's run or last week's?

# ── Stage 2: featurize ────────────────────────────────────────────────────────
# max_features=50000 is hardcoded — never recorded anywhere alongside the output
with open("train_raw.jsonl") as f:
    train_texts = [json.loads(l)["text"] for l in f]
vec = TfidfVectorizer(max_features=50000)
X_train = vec.fit_transform(train_texts)
pickle.dump(X_train, open("train_feats.pkl", "wb"))
pickle.dump(vec,     open("vectorizer.pkl",  "wb"))
# If this logic changes, all downstream models are silently stale — no alert

# ── Stage 3: train ────────────────────────────────────────────────────────────
# No record of which train_feats.pkl this model was trained on
X      = pickle.load(open("train_feats.pkl", "rb"))
y      = [r["label"] for r in train_records]  # train_records may be from a different run!
clf    = LogisticRegression(max_iter=500)
clf.fit(X, y)
pickle.dump(clf, open("model.pkl", "wb"))

# ── Stage 4: evaluate ─────────────────────────────────────────────────────────
with open("test_raw.jsonl") as f:
    test_texts = [json.loads(l)["text"] for l in f]
vec_loaded = pickle.load(open("vectorizer.pkl", "rb"))  # may be from a different featurize run!
X_test     = vec_loaded.transform(test_texts)
y_test     = [r["label"] for r in test_records]
preds      = clf.predict(X_test)
# Metrics printed to stdout — never stored, never linked to model.pkl
print(f"F1: {f1_score(y_test, preds, average='macro'):.3f}")
```

Problems visible above:

- `train_records` in Stage 3 may differ from what was written to `train_raw.jsonl` if any stage is re-run in isolation.

- `vectorizer.pkl` loaded in Stage 4 could be from an earlier featurize run with different `max_features`.

- F1 is printed but never persisted alongside `model.pkl`.

- There is no way to trace which `raw_corpus.jsonl` produced the model currently on disk.

**With CMF**, each stage is a `Context`, and each run is an `Execution`. Artifacts flow automatically:

```python
# Stage 1 - Parse
ctx_parse   = metawriter.create_context("parse")
exec_parse  = metawriter.create_execution("SplitData")
metawriter.log_dataset("raw_corpus.jsonl", "input")
metawriter.log_dataset("train_raw.jsonl",  "output")
metawriter.log_dataset("test_raw.jsonl",   "output")

# Stage 2 - Featurize
ctx_feat    = metawriter.create_context("featurize")
exec_feat   = metawriter.create_execution("TFIDFVectorizer", {"max_features": 50000})
metawriter.log_dataset("train_raw.jsonl",   "input")
metawriter.log_dataset("train_feats.npz",   "output")

# Stage 3 - Train
ctx_train   = metawriter.create_context("train")
exec_train  = metawriter.create_execution("BERTFinetune", {"epochs": 3, "lr": 2e-5})
metawriter.log_dataset("train_feats.npz", "input")
metawriter.log_model("bert_finetuned.pt", "output")

# Stage 4 - Evaluate
ctx_eval    = metawriter.create_context("evaluate")
exec_eval   = metawriter.create_execution("Evaluate")
metawriter.log_model("bert_finetuned.pt",   "input")
metawriter.log_dataset("test_feats.npz",    "input")
metawriter.log_execution_metrics("metrics", {"f1": 0.89, "precision": 0.91, "recall": 0.87})
```

The full lineage graph—from raw corpus to final F1 score—is automatically queryable through the Web UI or `CmfQuery`.

---
