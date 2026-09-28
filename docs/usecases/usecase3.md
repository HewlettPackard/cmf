**Scenario**: A company trains models at multiple edge locations (hospitals, factories) and needs to aggregate metadata centrally without sharing raw data.

**Without CMF**: Each site maintains local logs in incompatible formats. Merging them into a central view requires custom ETL.

```python
# ── Site A (Hospital) — logs to CSV ──────────────────────────────────────────
import csv, datetime, torch

def train_site_a(data_path, model_save_path):
    # ... training code ...
    auc = 0.91  # manually computed

    # Logged to a local CSV — schema invented by Site A's engineer
    with open("site_a_runs.csv", "a") as f:
        csv.writer(f).writerow([
            datetime.datetime.now().isoformat(),
            model_save_path,   # just a filename, no content hash
            data_path,         # just a path, could be overwritten tomorrow
            auc
        ])
    # Raw data never leaves Site A, but metadata is trapped here too

train_site_a("data/hospital_data.csv", "models/hospital_model.pt")


# ── Site B (Factory) — logs to JSONL with a different schema ─────────────────
import json

def train_site_b(checkpoint_path, input_file, metrics):
    # ... training code ...

    # Different key names, different nesting — incompatible with Site A
    entry = {
        "ts": str(datetime.datetime.now()),   # "ts" vs "timestamp" in Site A
        "checkpoint": checkpoint_path,        # "checkpoint" vs "model_save_path"
        "input_file": input_file,             # "input_file" vs "data_path"
        "results": metrics                    # nested dict vs flat columns
    }
    with open("site_b_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

train_site_b("chkpt_factory.pt", "factory_data_may.csv", {"auc": 0.88, "loss": 0.34})


# ── Central team tries to merge ───────────────────────────────────────────────
import pandas as pd

site_a = pd.read_csv("site_a_runs.csv",
                     names=["timestamp", "model_save_path", "data_path", "auc"])

site_b_records = []
with open("site_b_log.jsonl") as f:
    for line in f:
        r = json.loads(line)
        site_b_records.append({
            "timestamp":       r["ts"],              # rename to match Site A
            "model_save_path": r["checkpoint"],      # rename to match Site A
            "data_path":       r["input_file"],      # rename to match Site A
            "auc":             r["results"]["auc"]   # unnest to match Site A
        })
site_b = pd.DataFrame(site_b_records)

combined = pd.concat([site_a, site_b], ignore_index=True)
# ❌ No content hashes — cannot tell if hospital_data.csv and factory_data_may.csv
#    are related, or whether sites accidentally trained on the same underlying data.
# ❌ When Site C joins, this ETL script must be updated again.
# ❌ No way to verify data_path still points to the same file used during training.
print(combined)
```

Problems visible above:

- Site A uses flat CSV columns; Site B uses nested JSONL — the central team writes a manual ETL every time a new site is added.

- Paths like `hospital_data.csv` are just strings; if the file is overwritten, provenance is permanently lost.

- No content hashes mean it is impossible to tell whether two sites trained on identical data.

- Metrics are stored separately from model artifacts with no automated link between them.

**With CMF**:

- Each site runs CMF locally and tracks metadata to a local SQLite database.

- Periodically, each site runs `cmf metadata push` to the central CMF Server.

- The server merges metadata from all sites into a unified PostgreSQL database.

- No raw data ever leaves the site—only metadata (hashes, metrics, parameters) is transferred.

```
Site A (Hospital) ─── cmf metadata push ──▶ ┐
Site B (Factory)  ─── cmf metadata push ──▶ CMF Server ──▶ Unified Metadata DB
Site C (Research) ─── cmf metadata push ──▶ ┘                  ↕
                                                            CMF Web UI / Query API
```
