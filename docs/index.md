# Getting started with cmf

## Purpose and Scope

This document provides a comprehensive overview of the Common Metadata Framework (CMF), which implements a system for collecting, storing, and querying metadata associated with Machine Learning (ML) pipelines. CMF adopts a data-first approach where all artifacts (datasets, ML models, and performance metrics) are versioned and identified by their content hash, enabling distributed metadata tracking and collaboration across ML teams.

For detailed API documentation, see [Core Library (cmflib)](cmflib/index.md). For server deployment instructions, see [Installation & Setup](setup/index.md). For web user interface details, see [cmf-gui](ui/index.md).

## System Architecture

CMF is designed as a distributed system that enables ML teams to track pipeline metadata locally and synchronize with a central server. The framework automatically tracks code versions, data artifacts, and execution metadata to provide end-to-end traceability of ML experiments.

Common Metadata Framework (CMF) has the following components:

- **Metadata Library** exposes APIs to track pipeline metadata. It also provides APIs to query the stored metadata.
- **cmf-client** interacts with the cmf-server to pull or push metadata.
- **cmf-server with GUI** interacts with remote cmf-clients and merges the metadata transferred by each
  client. This server also provides a GUI that can render the stored metadata.
- **Central Artifact Repositories** host the code and data.

```mermaid
graph TB
    subgraph "Local Development Environment"
        CMF_CLIENT["**Metadata Library**<br/>cmflib.cmf.Cmf<br/>Main API Class"]
        CLI_TOOLS["**cmf-client**<br/>CLI Commands<br/>cmf init, push, pull"]
        LOCAL_MLMD[("Local MLMD<br/>SQLite Database")]
        DVC_GIT["DVC + Git<br/>Artifact Versioning"]
        NEO4J[("Neo4j<br/>Graph Database")]
    end

    subgraph "Central Infrastructure"
        CMF_SERVER["**cmf-server**<br/>FastAPI Application"]
        CENTRAL_MLMD[("PostgreSQL<br/>Central Metadata")]
        ARTIFACT_STORAGE[("Artifact Storage<br/>MinIO/S3/SSH")]
    end

    subgraph "Web Interface"
        REACT_UI["React Application<br/>Port 3000"]
        LINEAGE_VIZ["D3.js Lineage<br/>Visualization"]
        TENSORBOARD["TensorBoard<br/>Port 6006"]
    end

    CMF_CLIENT --> LOCAL_MLMD
    CMF_CLIENT --> DVC_GIT
    CMF_CLIENT --> NEO4J
    CLI_TOOLS --> CMF_SERVER
    CMF_SERVER --> CENTRAL_MLMD
    DVC_GIT --> ARTIFACT_STORAGE
    REACT_UI --> CMF_SERVER
    REACT_UI --> LINEAGE_VIZ
    CMF_SERVER --> TENSORBOARD
```

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

## Component Architecture

### CMF Library (`cmflib`)

The `cmflib` package provides the primary API for metadata tracking through the `Cmf` class and supporting modules:

```mermaid
graph TB
    subgraph "cmflib Package"
        CMF_CLASS["cmf.Cmf<br/>Main API Class"]
        METADATA_HELPER["metadata_helper.py<br/>MLMD Integration"]
        CMF_MERGER["cmf_merger.py<br/>Push/Pull Operations"]
        CMFQUERY["cmfquery.py<br/>Query Interface"]
        DATASLICE["dataslice.py<br/>Data Subset Tracking"]
    end

    subgraph "External Dependencies"
        MLMD[("ML Metadata<br/>SQLite/PostgreSQL")]
        DVC_SYSTEM["DVC<br/>Data Version Control"]
        GIT_SYSTEM["Git<br/>Code Version Control"]
        NEO4J_DB[("Neo4j<br/>Graph Database")]
    end

    CMF_CLASS --> METADATA_HELPER
    CMF_CLASS --> CMF_MERGER
    CMF_CLASS --> DATASLICE
    METADATA_HELPER --> MLMD
    CMF_CLASS --> DVC_SYSTEM
    CMF_CLASS --> GIT_SYSTEM
    CMF_CLASS --> NEO4J_DB
    CMF_MERGER --> CMFQUERY
```

### Server and Web Components

The CMF server provides centralized metadata storage and a web interface for exploring ML pipeline lineage:

```mermaid
graph TB
    subgraph "cmf-server"
        FASTAPI_SERVER["FastAPI Server<br/>Port 8080"]
        GET_DATA["get_data.py<br/>Data Access Layer"]
        LINEAGE_QUERY["Lineage Query<br/>D3 Visualization"]
    end

    subgraph "UI Components"
        REACT_APP["React Application<br/>ui/ directory"]
        ARTIFACTS_PAGE["Artifacts Page<br/>Browse Datasets/Models"]
        EXECUTIONS_PAGE["Executions Page<br/>Browse Pipeline Runs"]
        LINEAGE_PAGE["Lineage Visualization<br/>D3.js Graphs"]
    end

    subgraph "Storage Layer"
        POSTGRES[("PostgreSQL<br/>Central MLMD")]
        TENSORBOARD_LOGS[("TensorBoard Logs<br/>Training Metrics")]
    end

    FASTAPI_SERVER --> GET_DATA
    FASTAPI_SERVER --> LINEAGE_QUERY
    REACT_APP --> FASTAPI_SERVER
    REACT_APP --> ARTIFACTS_PAGE
    REACT_APP --> EXECUTIONS_PAGE
    REACT_APP --> LINEAGE_PAGE
    GET_DATA --> POSTGRES
    FASTAPI_SERVER --> TENSORBOARD_LOGS
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
