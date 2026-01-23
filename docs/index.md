# Getting started with CMF

## Purpose and Scope

This document provides a comprehensive overview of the Common Metadata Framework (CMF), which implements a system for collecting, storing, and querying metadata associated with Machine Learning (ML) pipelines. CMF adopts a data-first approach where all artifacts (datasets, ML models, and performance metrics) are versioned and identified by their content hash, enabling distributed metadata tracking and collaboration across ML teams.

For detailed API documentation, see [Core Library (CMFLib)](cmflib/index.md). For server deployment instructions, see [Installation & Setup](setup/index.md). For web user interface details, see [CMF GUI](ui/index.md).

## System Architecture

CMF is designed as a distributed system that enables ML teams to track pipeline metadata locally and synchronize with a central server. The framework automatically tracks code versions, data artifacts, and execution metadata to provide end-to-end traceability of ML experiments.


Common Metadata Framework (`CMF`) has the following components:

- **CMFLib**: A Python library that captures and tracks metadata throughout your ML pipeline, including datasets, models, and metrics. It provides APIs for both logging metadata during execution and querying it later for analysis.
- **CMF Client**: A command-line tool that synchronizes metadata with the `CMF Server`, manages artifact transfers to and from storage repositories, and integrates with Git for version control.
- **CMF Server with GUI**: A centralized server that aggregates metadata from multiple clients and provides a web-based graphical interface for visualizing pipeline executions, artifacts, and lineage relationships, enabling teams to collaborate effectively.
- **Central Artifact Repositories**: Storage backends (such as AWS S3, MinIO, or SSH-based storage) that host your datasets, models, and other pipeline artifacts.

<p align="center">
 <img src="../../assets/framework.png" height="400" align="center" />
</p>

## Core Abstractions

CMF uses three primary abstractions to model ML pipeline metadata:

| Abstraction | Purpose | Implementation |
|-------------|---------|----------------|
| **Pipeline** | Groups related stages and executions | Identified by name in `cmflib.cmf.Cmf` constructor |
| **Context** | Represents a stage type (e.g., "train", "test") | Created via `create_context()` method |
| **Execution** | Represents a specific run of a stage | Created via `create_execution()` method |

```mermaid
graph LR
    PIPELINE["Pipeline<br/>'mnist_experiment'"] --> CONTEXT1["Context<br/>'download'"]
    PIPELINE --> CONTEXT2["Context<br/>'train'"]
    PIPELINE --> CONTEXT3["Context<br/>'test'"]

    CONTEXT1 --> EXEC1["Execution<br/>'download_data'"]
    CONTEXT2 --> EXEC2["Execution<br/>'train_model'"]
    CONTEXT3 --> EXEC3["Execution<br/>'evaluate_model'"]

    EXEC1 --> DATASET1["Dataset<br/>'raw_data.csv'"]
    EXEC2 --> MODEL1["Model<br/>'trained_model.pkl'"]
    EXEC3 --> METRICS1["Metrics<br/>'accuracy: 0.95'"]
```

## Key Features

### Distributed Metadata Tracking

CMF enables distributed teams to work independently while maintaining consistent metadata through content-addressable artifacts and Git-like synchronization:

- **Local Development**: Each developer works with a local MLMD database
- **Content Hashing**: All artifacts are identified by their content hash for universal identification
- **Synchronization**: `cmf metadata push/pull` commands sync with central server
- **Artifact Storage**: Support for MinIO, Amazon S3, SSH, and local storage backends

### Automatic Version Tracking

CMF automatically captures:

- **Code Version**: Git commit IDs for reproducibility
- **Data Version**: DVC-managed artifact content hashes
- **Environment**: Execution parameters and custom properties
- **Lineage**: Input/output relationships between executions

### Query and Visualization

The system provides multiple interfaces for exploring metadata:

- **Programmatic**: `CmfQuery` class for custom queries
- **Web UI**: React-based interface for browsing artifacts and executions
- **Lineage Graphs**: D3.js visualizations showing data flow between pipeline stages
- **TensorBoard Integration**: Training metrics visualization
