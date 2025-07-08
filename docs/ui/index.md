# Getting Started with cmf-gui

The cmf-gui provides an intuitive, browser-based interface for exploring ML pipeline metadata, visualizing lineage relationships, and monitoring experiment progress. Built with React and D3.js, it offers interactive dashboards for artifacts, executions, and pipeline lineage.

## Artifacts and Executions Pages

The web interface provides dedicated pages for browsing and analyzing pipeline artifacts and executions.

### Artifacts Page

The Artifacts page allows users to explore all datasets, models, and metrics tracked by CMF:

```mermaid
graph TB
    subgraph "Artifacts Page Features"
        FILTER["Filter Panel<br/>• Type (Dataset/Model/Metrics)<br/>• Pipeline Name<br/>• Custom Properties"]
        TABLE["Artifacts Table<br/>• Name and Path<br/>• Type and Framework<br/>• Creation Time<br/>• Associated Pipeline"]
        DETAILS["Artifact Details<br/>• Properties and Metadata<br/>• Version History"]
        SEARCH["Search and Sort<br/>• Full-text Search<br/>• Column Sorting<br/>• Pagination<br/>"]
    end

    FILTER --> TABLE
    TABLE --> DETAILS
    TABLE --> SEARCH
```

#### Key Features

| Feature | Description | Usage |
|---------|-------------|-------|
| **Type Filtering** | Filter by artifact type | Select Dataset, Model, or Metrics |
| **Pipeline Filtering** | Filter by pipeline name | Choose from available pipelines |
| **Search** | Full-text search across metadata | Search names, properties, descriptions |
| **Sorting** | Sort by any column | Click column headers to sort |
| **Details View** | Detailed artifact information | Click artifact name for details |

#### Artifact Details

Each artifact provides comprehensive information:

- **Basic Information**: Name, type, creation time
- **Pipeline Context**: Associated pipeline, stage, and execution
- **Custom Properties**: User-defined metadata and labels
- **Version History**: All versions of the artifact with diffs

### Executions Page

The Executions page provides insights into pipeline runs and their performance:

```mermaid
graph TB
    subgraph "Executions Page Features"
        EXEC_FILTER["Execution Filters<br/>• Pipeline Name<br/>• Execution Type<br/>"]
        EXEC_TABLE["Executions Table<br/>• Execution ID and Name<br/>• Pipeline and Stage<br/>"]
        EXEC_DETAILS["Execution Details<br/>• Properties<br/>• Git Commit Information<br/>• Environment Details<br/>• Custom Properties"]
        EXEC_SEARCH["Search and Sort<br/>• Full-text Search<br/>• Column Sorting<br/>• Pagination<br/>"]
    end

    EXEC_FILTER --> EXEC_TABLE
    EXEC_TABLE --> EXEC_DETAILS
    EXEC_TABLE --> EXEC_SEARCH
```

#### Execution Information

Each execution entry displays:

- **Execution Metadata**: ID, name, type
- **Pipeline Context**: Pipeline name, stage, context information
- **Git Information**: Commit hash, branch, repository URL
- **Parameters**: Execution parameters and configuration

