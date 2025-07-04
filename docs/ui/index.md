# Web User Interface

The CMF Web User Interface provides an intuitive, browser-based interface for exploring ML pipeline metadata, visualizing lineage relationships, and monitoring experiment progress. Built with React and D3.js, it offers interactive dashboards for artifacts, executions, and pipeline lineage.

## Artifacts and Executions Pages

The web interface provides dedicated pages for browsing and analyzing pipeline artifacts and executions.

### Artifacts Page

The Artifacts page allows users to explore all datasets, models, and metrics tracked by CMF:

## Image #

#### Key Features

| Feature | Description | Usage |
|---------|-------------|-------|
| **Type Filtering** | Filter by artifact type | Select Dataset, Model, or Metrics |
| **Pipeline Filtering** | Filter by pipeline name | Choose from dropdown of available pipelines |
| **Date Range** | Filter by creation date | Use date picker for start/end dates |
| **Search** | Full-text search across metadata | Search names, properties, descriptions |
| **Sorting** | Sort by any column | Click column headers to sort |
| **Details View** | Detailed artifact information | Click artifact name for details |

#### Artifact Details

Each artifact provides comprehensive information:

- **Basic Information**: Name, type, creation time, file size
- **Pipeline Context**: Associated pipeline, stage, and execution
- **Custom Properties**: User-defined metadata and tags
- **Lineage Preview**: Immediate upstream/downstream relationships
- **Version History**: All versions of the artifact with diffs
- **Download Options**: Direct download links for artifact files

### Executions Page

The Executions page provides insights into pipeline runs and their performance:

## Image #

#### Execution Information

Each execution entry displays:

- **Execution Metadata**: ID, name, type, status, duration
- **Pipeline Context**: Pipeline name, stage, context information
- **Git Information**: Commit hash, branch, repository URL
- **Parameters**: Execution parameters and configuration
- **Artifacts**: Input and output artifacts with relationships
- **Logs**: Execution logs and error messages (if any)
- **Performance**: Resource usage and timing information

## Lineage Visualization

The lineage visualization system provides interactive, graph-based exploration of ML pipeline relationships using D3.js.

### Interactive Lineage Graph

## Image #

### Graph Elements

The lineage graph uses different visual elements to represent pipeline components:

#### Node Types

| Node Type | Visual Style | Represents |
|-----------|-------------|------------|
| **Dataset** | Blue circles | Input/output datasets |
| **Model** | Green rectangles | ML models |
| **Metrics** | Orange diamonds | Performance metrics |
| **Execution** | Purple hexagons | Pipeline executions |

#### Edge Types

| Edge Type | Visual Style | Represents |
|-----------|-------------|------------|
| **Input** | Solid blue arrow | Data flow into execution |
| **Output** | Solid green arrow | Data flow from execution |
| **Dependency** | Dashed gray line | Execution dependencies |

### Visualization Features

#### Interactive Navigation

- **Pan and Zoom**: Mouse drag to pan, scroll wheel to zoom
- **Node Selection**: Click nodes to view details in sidebar
- **Multi-select**: Ctrl+click to select multiple nodes
- **Context Menu**: Right-click for node-specific actions

#### Layout Options

```javascript
// Available layout algorithms
const layouts = {
  "hierarchical": "Top-down hierarchical layout",
  "force": "Force-directed physics simulation", 
  "circular": "Circular arrangement of nodes",
  "grid": "Grid-based positioning",
  "timeline": "Chronological timeline layout"
};
```

#### Filtering and Search

- **Node Type Filter**: Show/hide specific node types
- **Pipeline Filter**: Focus on specific pipeline stages
- **Date Range Filter**: Filter by execution time
- **Property Search**: Search by node properties
- **Path Highlighting**: Highlight paths between selected nodes

### Lineage Analysis

#### Upstream Analysis

Trace data lineage backwards to understand data sources:

## Image #

#### Downstream Analysis

Trace forward to see how artifacts are used:

## Image#

#### Impact Analysis

Understand the impact of changes:

- **Change Propagation**: See which artifacts are affected by changes
- **Dependency Analysis**: Identify critical path dependencies
- **Version Comparison**: Compare different versions of pipelines
- **Performance Tracking**: Track performance changes over time

### TensorBoard Integration

The web interface seamlessly integrates with TensorBoard for detailed training metrics visualization.

#### TensorBoard Features

## Image #

#### Integration Points

- **Automatic Discovery**: CMF automatically detects TensorBoard logs
- **Embedded Viewer**: TensorBoard embedded directly in CMF interface
- **Synchronized Navigation**: Navigate between CMF lineage and TensorBoard
- **Metric Correlation**: Correlate TensorBoard metrics with CMF artifacts

#### Usage Example

```python
# Log TensorBoard data in CMF
import tensorflow as tf
from cmflib import cmf

# Initialize CMF and TensorBoard
cmf_instance = cmf.Cmf(filename="mlmd", pipeline_name="training")
writer = tf.summary.create_file_writer("logs/train")

# Training loop with CMF and TensorBoard logging
for epoch in range(num_epochs):
    # Train model
    loss = train_step()
    
    # Log to TensorBoard
    with writer.as_default():
        tf.summary.scalar('loss', loss, step=epoch)
    
    # Log to CMF
    cmf_instance.log_metrics(
        metrics_name=f"epoch_{epoch}_metrics",
        custom_properties={"loss": loss, "epoch": epoch}
    )

# CMF automatically links TensorBoard logs
cmf_instance.log_tensorboard_logs("logs/train")
```

### Dashboard Configuration

The web interface supports customizable dashboards:

#### Widget Types

- **Metric Cards**: Key performance indicators
- **Timeline Charts**: Execution timelines and durations
- **Artifact Counters**: Counts by type and status
- **Pipeline Status**: Current pipeline health
- **Recent Activity**: Latest executions and artifacts

#### Customization Options

- **Layout**: Drag and drop widget arrangement
- **Filters**: Dashboard-level filters and time ranges
- **Themes**: Light/dark mode and color schemes
- **Export**: Export dashboards as PDF or images
- **Sharing**: Share dashboard configurations with team
