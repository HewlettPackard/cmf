# CMF Use Cases: Optimizing Machine Learning Pipelines

## 1. Overview

The **Common Metadata Framework (CMF)** is a metadata tracking and versioning system purpose-built for ML pipelines. It captures code versions, data artifacts, execution parameters, and performance metrics—providing a unified, queryable, and shareable record of every experiment across distributed teams.

This document describes real-world use cases for CMF, explains how ML pipelines operate **with** and **without** CMF, and provides a detailed comparison to help teams understand where CMF delivers value.

---

## 2. The Problem: ML Pipelines Without CMF

In a typical unmanaged ML workflow, teams rely on ad-hoc practices to track experiments, data, and models. This leads to a range of operational and reproducibility problems.

### 2.1 Typical Unmanaged ML Pipeline

```
Raw Data → Preprocessing → Feature Engineering → Model Training → Evaluation → Deployment
   ↓             ↓                  ↓                  ↓              ↓            ↓
 manual        manual             manual             manual          manual      manual
 copies      notebooks          CSV files          .pkl saves    spreadsheets   scripts
```

**Common pain points:**

- **No lineage**: Impossible to trace which data version produced which model.
- **Manual bookkeeping**: Teams use spreadsheets, notebooks, or comments to log parameters and metrics.
- **Reproducibility failure**: Re-running an "old experiment" is unreliable because data, code, or environment may have changed silently.
- **Collaboration gaps**: Metadata stays on individual laptops; team members cannot see each other's runs.
- **Storage waste**: Multiple copies of datasets are saved under ad-hoc names (`data_v1_final_REAL.csv`).
- **No distributed tracking**: Edge/cloud/datacenter nodes produce metadata that never gets consolidated.

---

## 3. The Solution: ML Pipelines With CMF

CMF introduces a **structured metadata layer** over the entire pipeline. Every stage, artifact, and parameter is automatically versioned and tracked in a queryable store.

### 3.1 CMF-Managed ML Pipeline

```
Raw Data → Preprocessing → Feature Engineering → Model Training → Evaluation → Deployment
   ↓             ↓                  ↓                  ↓              ↓            ↓
 cmf.log_    cmf.log_          cmf.log_           cmf.log_       cmf.log_     cmf.log_
 dataset()   dataset()         dataset()           model()       metrics()    execution()
             + DVC hash        + DVC hash          + Git SHA     + artifact
                                                                   linkage
       ↓_______________↓_________________↓__________________↓___________↓___________↓
                                   CMF Metadata Store (SQLite / PostgreSQL)
                                              ↕
                                     cmf metadata push/pull
                                              ↕
                                       CMF Server + Web UI
```

**What changes:**

- Artifacts are identified by **content hash** (via DVC), not file names.
- Code is tied to a **Git commit SHA** automatically.
- Execution parameters, environment info, and custom properties are logged per-run.
- All metadata is **queryable** and **syncable** across teams and environments.

---

## 4. Comparison Chart: ML Pipeline With vs. Without CMF

| Aspect | Without CMF | With CMF |
|--------|-------------|----------|
| **Artifact versioning** | Manual copies, ad-hoc naming | Content-addressable hashing via DVC |
| **Code versioning** | Developer must remember to note Git SHA | Automatically captured per execution |
| **Experiment tracking** | Spreadsheets, notebooks, comments | Structured metadata store (SQLite/PostgreSQL) |
| **Reproducibility** | Often broken; dependencies implicit | Full lineage: data + code + params per run |
| **Data lineage** | Not tracked | Input/output artifact graph per stage |
| **Collaboration** | Metadata siloed on individual machines | Push/pull metadata like Git branches |
| **Distributed execution** | Incompatible log formats per site; custom ETL required to consolidate metadata centrally | Metadata synced across CMF servers via the **Metahub** feature using push/pull metadata functionality |
| **Model traceability** | Hard to link model back to training data | Every model artifact links to exact dataset hash + execution |
| **Querying metadata** | Manual search through logs/files | `CmfQuery` API or Web UI for structured queries |
| **Visualization** | Custom scripts or none | Built-in lineage graphs, Web UI dashboards |
| **Storage efficiency** | Duplicate dataset files across runs | Deduplicated artifacts by content hash |
| **Audit & compliance** | Difficult to reconstruct history | Full immutable execution history |
| **API access** | None (or custom solutions) | REST API + MCP Server for AI assistant access |
| **Multi-stage pipelines** | Manual orchestration notes | Contexts and executions map each stage automatically |
| **Onboarding new members** | Share notebooks / explain verbally | Pull metadata + artifacts; instantly see full history |

---

## 5. Use Cases

1. [Reproducible Experiment Management](./usecase1.md)
2. [Multi-Stage Pipeline Tracking](./usecase2.md)
3. [Distributed / Federated ML](./usecase3.md)
4. [Dataset Deduplication and Storage Optimization](./usecase4.md)
