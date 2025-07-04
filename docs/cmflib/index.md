# Core Library (cmflib)

The `cmflib` package is the foundational Python library that provides the core metadata tracking capabilities for the Common Metadata Framework (CMF). It offers a unified API for logging metadata across distributed AI/ML pipelines, integrating with multiple storage backends and versioning systems.

This document covers the core library components, main API classes, and integration mechanisms. For CLI usage patterns, see [Command Line Interface](#command-line-interface). For server-side components, see [CMF Server](../server/index.md). For deployment configurations, see [Server Deployment](../server/index.md#server-deployment).

## Core Architecture

The `cmflib` library follows a modular architecture centered around the main `Cmf` class, with specialized components for different aspects of metadata management.

### Library Structure

```mermaid
graph TB
    subgraph "Public API Layer"
        Cmf_Class["Cmf<br/>(cmf.py)"]
        CLI_Wrapper["cmf_commands_wrapper"]
        Query_API["cmfquery.py"]
    end
    
    subgraph "Core Operations"
        Metadata_Helper["metadata_helper.py<br/>MLMD Operations"]
        CMF_Merger["cmf_merger.py<br/>Push/Pull Logic"]
        CMF_Server["cmf_server.py<br/>Server Integration"]
    end
    
    subgraph "Storage Backends"
        SQLite_Store["SqlliteStore"]
        Postgres_Store["PostgresStore"] 
        DVC_Wrapper["dvc_wrapper.py<br/>Git/DVC Integration"]
    end
    
    subgraph "External Integrations"
        Graph_Wrapper["graph_wrapper.py<br/>Neo4j Integration"]
        Utils["utils/<br/>helper_functions.py<br/>cmf_config.py"]
    end
    
    subgraph "Storage Systems"
        MLMD_DB[("ML Metadata Store<br/>SQLite/PostgreSQL")]
        Neo4j_DB[("Neo4j Graph DB")]
        Artifact_Store[("Artifact Storage<br/>S3/MinIO/SSH/Local")]
        Git_Repo[("Git Repository")]
    end
    
    %% API connections
    Cmf_Class --> Metadata_Helper
    Cmf_Class --> CMF_Merger
    Cmf_Class --> DVC_Wrapper
    Cmf_Class --> Graph_Wrapper
    
    %% Storage connections  
    Metadata_Helper --> SQLite_Store
    Metadata_Helper --> Postgres_Store
    SQLite_Store --> MLMD_DB
    Postgres_Store --> MLMD_DB
    
    %% External connections
    DVC_Wrapper --> Artifact_Store
    DVC_Wrapper --> Git_Repo
    Graph_Wrapper --> Neo4j_DB
    
    %% Integration connections
    CLI_Wrapper --> Cmf_Class
    CMF_Server --> Cmf_Class
    Query_API --> MLMD_DB
```

## Main API (cmf.Cmf)

The `Cmf` class is the primary interface for metadata tracking in CMF. It provides methods for creating pipelines, contexts, executions, and logging artifacts.

### Key Methods

| Method | Purpose | Usage |
|--------|---------|-------|
| `__init__(filename, pipeline_name)` | Initialize CMF instance | `cmf = Cmf(filename="mlmd", pipeline_name="my_pipeline")` |
| `create_context(pipeline_stage)` | Create a pipeline stage context | `context = cmf.create_context(pipeline_stage="train")` |
| `create_execution(execution_type)` | Create an execution within a context | `execution = cmf.create_execution(execution_type="training_run")` |
| `log_dataset(url, event, custom_properties)` | Log dataset artifacts | `cmf.log_dataset(url="data.csv", event="input")` |
| `log_model(path, event, model_framework)` | Log model artifacts | `cmf.log_model(path="model.pkl", event="output")` |
| `log_metrics(metrics_name, custom_properties)` | Log metrics | `cmf.log_metrics(metrics_name="accuracy", custom_properties={"value": 0.95})` |

### Basic Usage Example

```python
from cmflib import cmf

# Initialize CMF
cmf_instance = cmf.Cmf(filename="mlmd", pipeline_name="mnist_pipeline")

# Create context and execution
context = cmf_instance.create_context(pipeline_stage="train")
execution = cmf_instance.create_execution(execution_type="training")

# Log artifacts
cmf_instance.log_dataset(url="train_data.csv", event="input")
cmf_instance.log_model(path="trained_model.pkl", event="output", 
                      model_framework="sklearn")
cmf_instance.log_metrics(metrics_name="accuracy", 
                        custom_properties={"value": 0.95, "epoch": 10})
```

## Metadata Operations

CMF provides comprehensive metadata operations for tracking ML pipeline artifacts and their relationships.

### Artifact Types

CMF supports three primary artifact types:

1. **Datasets**: Input/output data files with versioning
2. **Models**: ML models with framework-specific metadata
3. **Metrics**: Performance metrics and custom properties

### Execution Tracking

Each execution automatically captures:
- **Git commit hash**: For code reproducibility
- **Execution parameters**: Custom properties and configurations
- **Timestamps**: Start and end times
- **Environment**: Python environment and dependencies

## Command Line Interface

CMF provides a comprehensive CLI for managing metadata and artifacts:

### Core Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `cmf init` | Initialize CMF configuration | `cmf init --type=local` |
| `cmf metadata push` | Push metadata to server | `cmf metadata push --pipeline-name=my_pipeline` |
| `cmf metadata pull` | Pull metadata from server | `cmf metadata pull --pipeline-name=my_pipeline` |
| `cmf artifact push` | Push artifacts to storage | `cmf artifact push --pipeline-name=my_pipeline` |
| `cmf artifact pull` | Pull artifacts from storage | `cmf artifact pull --pipeline-name=my_pipeline` |

### Configuration Management

```bash
# Initialize local configuration
cmf init --type=local

# Initialize with server configuration
cmf init --type=server --url=http://cmf-server:8080

# Configure artifact storage
cmf init --type=s3 --endpoint-url=http://minio:9000 --access-key-id=minioadmin
```

## Storage Backends

CMF supports multiple storage backends for artifacts and metadata:

### Metadata Storage

- **SQLite**: Local development and single-user scenarios
- **PostgreSQL**: Production deployments and multi-user environments

### Artifact Storage

- **Local**: File system storage for development
- **Amazon S3**: Cloud storage with versioning
- **MinIO**: Self-hosted S3-compatible storage
- **SSH**: Remote server storage via SSH

### Configuration Examples

```python
# Local storage
cmf_instance = cmf.Cmf(
    filename="mlmd",
    pipeline_name="my_pipeline",
    graph=False  # Disable Neo4j for local development
)

# Server-based storage
cmf_instance = cmf.Cmf(
    filename="postgresql://user:pass@server:5432/mlmd",
    pipeline_name="my_pipeline",
    graph=True,
    neo4j_uri="bolt://neo4j:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
```

## External Integrations

### Git Integration

CMF automatically integrates with Git to track code versions:

- **Commit tracking**: Automatically captures Git commit hashes
- **Branch information**: Records current branch and remote URL
- **Diff tracking**: Can optionally store code diffs

### DVC Integration

Data Version Control (DVC) integration provides:

- **Data versioning**: Content-based versioning of datasets
- **Remote storage**: Integration with cloud storage providers
- **Pipeline tracking**: DVC pipeline stage integration

### Neo4j Integration

Graph database integration enables:

- **Lineage visualization**: Interactive pipeline lineage graphs
- **Relationship queries**: Complex queries across pipeline relationships
- **Performance analytics**: Graph-based performance analysis

### Example Integration Setup

```python
from cmflib import cmf

# Full integration setup
cmf_instance = cmf.Cmf(
    filename="postgresql://user:pass@server:5432/mlmd",
    pipeline_name="production_pipeline",
    graph=True,
    neo4j_uri="bolt://neo4j:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    git_repo="/path/to/repo",
    is_server=True
)

# Enable automatic Git tracking
cmf_instance.log_execution_metrics_from_client()
```
