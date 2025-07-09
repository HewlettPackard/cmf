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

CMF tracks pipeline stages, inputs/outputs, metrics, and code. It supports decentralized execution across datacenters, edge, and cloud.

- Artifacts are versioned using DVC (`.dvc` files).
- Code is tracked with Git.
- Metadata is logged to relational DB (e.g., SQLite, PostgreSQL)
- Sync metadata with `cmf metadata push` and `cmf metadata pull`.

---

## 🏛 Architecture

CMF is composed of:

- **cmflib** - metadata library provides API to log/query metadata
- **cmf-client** – CLI to sync metadata with server, push/pull artifacts to the user-specified repo, push/pull code from git.
- **cmf-server** – REST API for metadata merge
- **Central Repositories** – Git (code), DVC (artifacts), CMF (metadata)

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
from ml_metadata.proto import metadata_store_pb2 as mlpb
cmf = Cmf(filepath="mlmd", pipeline_name="test_pipeline")
context: mlpb.proto.Context = cmf.create_context(
    pipeline_stage="prepare",
    custom_properties ={"user-metadata1": "metadata_value"}
)
execution: mlpb.proto.Execution = cmf.create_execution(
    execution_type="Prepare",
    custom_properties = {"split": split, "seed": seed}
)
artifact: mlpb.proto.Artifact = metawriter.log_dataset(
	"artifacts/data.xml.gz", "input",
	custom_properties={"user-metadata1": "metadata_value"}
)
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
- Scalable metadata syncing
- Team collaboration on metadata

---

## 🎤 Talks & Publications

- 🎙 [Monterey Data Conference 2022](https://drive.google.com/file/d/1Oqs0AN0RsAjt_y9ZjzYOmBxI8H0yqSpB/view)

---

## 🌐 Related Projects

- [📚 Common Metadata Ontology](https://hewlettpackard.github.io/cmf/common-metadata-ontology/readme/)
- [🧠 AI Metadata Knowledge Graph (AIMKG)](https://github.com/HewlettPackard/ai-metadata-knowledge-graph)
---

## 🤝 Community

- 💬 [Join CMF on Slack](https://commonmetadata.slack.com/)
- 📧 Contact: **annmary.roy@hpe.com**

---

## 📄 License

Licensed under the [Apache 2.0 License](./LICENSE)

---

> © Hewlett Packard Enterprise. Built for reproducibility in ML.
