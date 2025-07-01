# Common Metadata Framework (CMF)

[![CI](https://github.com/HewlettPackard/cmf/actions/workflows/ci.yml/badge.svg)](https://github.com/HewlettPackard/cmf/actions)
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

📖 Follow the guide in [`docs/cmf_server/cmf-server.md`](docs/cmf_server/cmf-server.md)

---

## 📘 Documentation

- [Getting Started](https://hewlettpackard.github.io/cmf/)
- [API Reference](https://hewlettpackard.github.io/cmf/api/public/cmf)
- [Full Docs](./docs/README.md)
- [Related Docs](https://deepwiki.com/HewlettPackard/cmf)

---

## 🧠 How It Works

CMF tracks pipeline stages, inputs/outputs, metrics, and code. It supports decentralized execution across datacenters, edge, and cloud. Journaling enables sync when offline.

- Artifacts are versioned using DVC (`.dvc` files)
- Code is tracked with Git
- Metadata is logged to relational DB (e.g., SQLite, MLMD)
- Sync metadata with `cmf push` and `cmf pull`

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
cmf                          # Comprehensive tool designed to initialize an artifact repository and perform various operations on artifacts, execution, pipeline and metadata
cmf init                     # Initialize an artifact repository for cmf. Local directory, Minio S3 bucket, Amazon S3 bucket, SSH Remote and Remote OSDF directory are the options available
cmf init show                # Display current cmf configuration
cmf metadata push            # Push the metadata file from the local machine to the cmf-serve
cmf metadata pull            # Pull the metadata file from the cmf-server to the user's local machine

```
Please read our [Command Reference](https://hewlettpackard.github.io/cmf/docs/cmf_client.md) for a complete list.
---

## ✅ Benefits

- Full ML pipeline observability
- Unified metadata, artifact, and code tracking
- Supports disconnected/offline data centers
- Scalable metadata syncing
- Team collaboration on metadata

---

## 🎤 Talks & Publications

- 🎙 [Monterey Data Conference 2022](https://drive.google.com/file/d/1Oqs0AN0RsAjt_y9ZjzYOmBxI8H0yqSpB/view)
- 📄 *Constructing a Metadata Knowledge Graph as an Atlas of ML Pipelines* – [Frontiers in Big Data, 2025](https://www.frontiersin.org/articles/10.3389/fdata.2024.1176506/full)

---

## 🌐 Related Projects

- [📚 Common Metadata Ontology](https://hewlettpackard.github.io/cmf/common-metadata-ontology/readme/)
- [🧠 AI Metadata Knowledge Graph (AIMKG)](https://github.com/HewlettPackard/ai-metadata-knowledge-graph)
- [📦 CMF Plugin for DVC](LINK_TO_PLUGIN_IF_ANY)

---

## 🤝 Community

- 💬 [Join CMF on Slack](https://commonmetadata.slack.com/)
- 📧 Contact: **annmary.roy@hpe.com**

---

## 📄 License

Licensed under the [Apache 2.0 License](./LICENSE)

---

> © Hewlett Packard Enterprise. Built for reproducibility in ML.
