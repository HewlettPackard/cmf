# Common Metadata Framework (CMF)

[![Deploy Docs](https://github.com/HewlettPackard/cmf/actions/workflows/deploy_docs_to_gh_pages.yaml/badge.svg)](https://github.com/HewlettPackard/cmf/actions)
[![PyPI version](https://badge.fury.io/py/cmflib.svg)](https://pypi.org/project/cmflib/)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://hewlettpackard.github.io/cmf/)
[![License](https://img.shields.io/github/license/HewlettPackard/cmf)](./LICENSE)

**Common Metadata Framework (CMF)** is a metadata tracking and versioning system for ML pipelines. It tracks code, data, and pipeline metrics—offering Git-like metadata management across distributed environments.

---

## 🚀 Features

- ✅ Track artifacts (datasets, models, metrics) using content-based hashes  
- ✅ Automatically logs code versions (Git) and data versions (DVC)  
- ✅ Push/pull metadata via CLI across distributed sites  
- ✅ REST API for direct server interaction  
- ✅ Implicit & explicit tracking of pipeline execution  
- ✅ Fine-grained or coarse-grained metric logging  

---

## 📦 Installation

### Requirements

- Linux/Ubuntu/Debian
- Python >=3.9, <3.11
- Git (latest)

### Virtual Environment

<details><summary>Conda</summary>

```bash
conda create -n cmf python=3.10
conda activate cmf
```
</details>

<details><summary>Virtualenv</summary>

```bash
virtualenv --python=3.10 .cmf
source .cmf/bin/activate
```
</details>

### Install CMF

<details><summary>Latest from GitHub</summary>

```bash
pip install git+https://github.com/HewlettPackard/cmf
```
</details>

<details><summary>Stable from PyPI</summary>

```bash
pip install cmflib
```
</details>

### Server Setup

📖 Follow the guide in <a href="docs/cmf_server/cmf-server.md" target="_blank">docs/cmf_server/cmf-server.md</a>

---

## 📘 Documentation

- [Getting Started](https://hewlettpackard.github.io/cmf/)
- [API Reference](https://hewlettpackard.github.io/cmf/api/public/cmf)
- [Full Docs](./docs/README.md)
- [Command Reference](https://hewlettpackard.github.io/cmf/cmf_client/cmf_client)
- [Related Docs](https://deepwiki.com/HewlettPackard/cmf)

---

## 🧠 How It Works

CMF tracks pipeline stages, inputs/outputs, metrics, and code. It supports decentralized execution across datacenters, edge, and cloud. Journaling enables sync when offline.

- Artifacts are versioned using DVC (`.dvc` files)
- Code is tracked with Git
- Metadata is logged to relational DB (e.g., SQLite, MLMD)
- Sync metadata with `cmf metadata push` and `cmf metadata pull`

---

## 🏛 Architecture

CMF is composed of:

- **Metadata Library** – API to log/query metadata
- **Client** – CLI to sync metadata with server
- **Server** – REST API for metadata merge
- **Central Stores** – Git (code), DVC (artifacts), CMF (metadata)

<p align="center">
  <img src="docs/assets/framework.png" height="350" />
</p>

<p align="center">
  <img src="docs/assets/distributed_architecture.png" height="300" />
</p>

---

## 🔧 Sample Usage

```python
from cmflib.cmf import Cmf

cmf = Cmf(filename="mlmd", pipeline_name="demo")
ctx = cmf.create_context(pipeline_stage="train")
cmf.log_artifact(uri="data.csv", artifact_type="dataset", is_input=True)
cmf.log_metrics({"accuracy": 0.95})
```

```bash
cmf                          # CLI to manage metadata and artifacts
cmf init                     # Initialize artifact repository
cmf init show                # Show current CMF config
cmf metadata push            # Push metadata to server
cmf metadata pull            # Pull metadata from server
```
	
➡️ For the complete list of commands, please refer to the <a href="https://hewlettpackard.github.io/cmf/cmf_client/cmf_client">Command Reference</a>


---

## ✅ Benefits

- Full ML pipeline observability
- Unified metadata, artifact, and code tracking
- Supports disconnected/offline data centers
- Scalable metadata syncing
- Team collaboration on metadata

---

## 🎤 Talks & PublicationsAdd commentMore actions

- 🎙 [Monterey Data Conference 2022](https://drive.google.com/file/d/1Oqs0AN0RsAjt_y9ZjzYOmBxI8H0yqSpB/view)
- 📄 *Constructing a Metadata Knowledge Graph as an Atlas of ML Pipelines* – [Frontiers in Big Data, 2025](https://www.frontiersin.org/articles/10.3389/fdata.2024.1176506/full)

---

## 🌐 Related Projects

- [📚 Common Metadata Ontology](https://hewlettpackard.github.io/cmf/common-metadata-ontology/readme/)
- [🧠 AI Metadata Knowledge Graph (AIMKG)](https://github.com/HewlettPackard/ai-metadata-knowledge-graph)
---

## 🤝 CommunityAdd commentMore actions

- 💬 [Join CMF on Slack](https://commonmetadata.slack.com/)
- 📧 Contact: **annmary.roy@hpe.com**

---

## 📄 License

Licensed under the [Apache 2.0 License](./LICENSE)

---

> © Hewlett Packard Enterprise. Built for reproducibility in ML.
