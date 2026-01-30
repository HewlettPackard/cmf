# Getting Started with CMF GUI

The CMF GUI provides an intuitive, browser-based interface for exploring ML pipeline metadata, visualizing lineage relationships, and synchronizing metadata between multiple CMF servers. Built with React and D3.js, it offers interactive dashboards for artifacts, executions, and pipeline lineage.

## Overview

The CMF GUI consists of several main sections:

- **[Artifacts](artifacts.md)**: Browse and search datasets, models, and metrics
- **[Executions](executions.md)**: View pipeline runs and execution history
- **[Lineage](lineage.md)**: Visualize data flow and dependencies
- **[Metahub](../cmf_server/metahub-tab-usage.md)**: Synchronize metadata between CMF servers
- **[TensorBoard](../cmf_client/tensorflow_guide.md)**: View ML training metrics

---

## Quick Start

### Accessing the CMF GUI

1. Ensure the [CMF Server is running](../setup/index.md#install-cmf-server-with-gui)
2. Open your browser and navigate to the server URL (default: `http://your-server-ip:80`)
3. The GUI will display the available pipelines in the sidebar

---

## Artifacts View

The Artifacts page displays all datasets, models, and metrics tracked by CMF. You can browse, search, and explore artifact metadata, versions, and lineage.

### Key Features

- **Artifact Listing**: View all artifacts with their types (Dataset, Model, Metrics)
- **Search & Filter**: Find specific artifacts by name, type, or properties
- **Artifact Details**: Examine metadata, custom properties, and version information

![CMF Artifacts Page](../assets/artifacts.jpeg)

---

## Executions View

The Executions page displays all pipeline runs and execution history. You can view execution details, parameters, and associated artifacts for each run.

### Key Features

- **Execution History**: View all past executions with timestamps
- **Execution Details**: See parameters, properties, and metadata for each run
- **Filtering & Search**: Find specific executions by name, type, or properties

![CMF Executions Page](../assets/executions.png)

---

## Lineage Visualization

The Lineage page offers interactive visualizations of data flow and dependencies in your ML pipelines. It provides following different visualization modes:

### Visualization Types

1. **Artifact Lineage**: Hierarchical view of artifact dependencies
2. **Execution Lineage**: Hierarchical view of execution flow
3. **Artifact-Execution Lineage**: Combined view showing both artifacts and executions

![CMF ArtifactExecution Page](../assets/ArtifactExecutionLineage.png)

---

## Metahub

The [Metahub](../cmf_server/metahub-tab-usage.md) feature enables synchronization of metadata between two CMF servers, allowing distributed teams to collaborate and share ML pipeline metadata.

---

## TensorBoard Integration

CMF integrates with [TensorBoard](../cmf_client/tensorflow_guide.md) to visualize training metrics, model graphs, and other ML-specific visualizations alongside CMF metadata.

---

## Prerequisites

Before using the CMF GUI, ensure you have:

1. **CMF Server Running**: Follow the [installation guide](../setup/index.md#install-cmf-server-with-gui)
2. **Metadata Pushed**: Use `cmf metadata push` to send metadata to server
3. **Browser Compatibility**: Modern browser (Chrome, Firefox, Safari, Edge)

---

## Getting Help

- For API details, see [CMFLib Documentation](../cmflib/index.md)
- For CLI commands, see [CMF Client Commands](../cmf_client/cmf_client_commands.md)
- For server setup, see [Installation & Setup](../setup/index.md)