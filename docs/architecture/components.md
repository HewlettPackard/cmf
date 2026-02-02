## cmflib

The APIs and abstractions provided by `cmflib` enable tracking of pipeline metadata. 

`cmflib` tracks the stages in the pipeline, the input and output artifacts at each stage, and metrics. 

The framework allows metrics to be tracked at both coarse and fine-grained intervals. Stage metrics can be captured at the end of a stage, while fine-grained metrics can be tracked per step (epoch) or at regular intervals during the execution of the stage. 

The metadata logged through the APIs is written to a backend relational database. `cmflib` also provides APIs to query the metadata stored in the relational database, allowing users to inspect pipelines.   

In addition to explicit tracking through the APIs, `cmflib` provides implicit tracking. This automatically tracks the software version used in the pipelines.  

All artifacts are versioned using a data versioning framework (e.g., DVC). The content hash of the artifacts is generated and stored along with the user-provided metadata. A special artifact metadata file called a ".dvc" file is created for every artifact (file or folder) that is added to the data version management system. The .dvc file contains the content hash of the artifact.

For every pipeline, the metadata tracker creates a new branch to track the code. 

The special metadata file created for artifacts, “.dvc” file is too committed to Git. Whenever there is a change in the artifact, the metadata file is modified to reflect its current content hash, and the file is tracked as a new version in the metadata file.  

## CMF Client 

The CMF Client interacts with the CMF Server for metadata synchronization.  

After the experiment is completed, the user invokes the `cmf push` command to push the collected metadata to the CMF Server. This transfers the existing metadata journal to the server.  

The metadata from the CMF Server can be pulled to the local repository using `cmf metadata` command.

When an artifact is used as the identifier, all metadata associated with the artifacts currently present in the branch of the cloned Git repository is pulled from the central repository to the local repository. 

When a project is used as the identifier, all the metadata associated with the current branch of the pipeline code that is checked out is pulled to the local repository. 

## CMF Server with GUI

The CMF Server serves as the central hub for metadata management and visualization in the Common Metadata Framework. It exposes REST APIs that are used to push/pull metadata and view different types of lineage. 

The CMF Server provides two primary interfaces:

### REST API Layer

The server exposes a comprehensive set of REST API endpoints for:

- **Metadata Synchronization**: Push and pull metadata from distributed sites
- **Artifact Queries**: Retrieve artifact information, lineage, and properties
- **Execution Queries**: Access execution details, logs, and relationships
- **Lineage Retrieval**: Generate various lineage graphs (artifact, execution, and combined views)
- **Pipeline Management**: List pipelines, executions, and associated artifacts

These APIs enable programmatic access to the metadata repository and support integration with various tools and workflows.

### Web-Based GUI

The CMF Server includes a comprehensive web interface that provides visual access to tracked metadata:

**Key Pages:**

- **Artifacts Page**: Browse and search all artifacts (datasets, models, metrics) across pipelines with filtering, sorting, and detailed metadata views
- **Executions Page**: View pipeline execution history, execution parameters, Git commit information, and execution status
- **Lineage Page**: Interactive visualizations of data flow and dependencies through multiple view modes:

  - Artifact Tree: Hierarchical view of artifact dependencies
  - Execution Tree: Pipeline stage execution flow
  - Artifact-Execution Tree: Combined view showing complete provenance
  - Force-Directed Graph: Network visualization of complex relationships

**Capabilities:**

- Real-time metadata visualization from centralized repository
- Interactive lineage graphs with zoom, pan, and node inspection
- Search and filter capabilities across all metadata types
- Version tracking and artifact comparison
- Pipeline execution monitoring and debugging

The GUI enables users to understand pipeline structure, trace data provenance, debug execution issues, and analyze relationships between artifacts without writing code.

## Central Repositories 

The Common Metadata Framework (CMF) consists of three central repositories for code, data, and metadata. 

### Central Metadata Repository

The central metadata repository holds the metadata pushed from distributed sites. It stores metadata about all the different pipelines that were tracked using the common metadata tracker. 

The consolidated view of the metadata stored in the central repository helps users learn across various stages of the pipeline executed at different locations. 


### Central Artifact Storage Repository 

The central artifact storage repository stores all the artifacts related to experiments. The data versioning framework (i.e. DVC) stores the artifacts in a content-addressable layout. The artifacts are stored inside folders named with the first two characters of the content hash, and the artifact filename is the remaining part of the content hash. This layout enables efficient retrieval of artifacts.   

### Git Repository 

The Git repository is used to track the code. Along with the code, the metadata files of the artifacts (which contain the content hash of the artifacts) are also stored in Git. The data versioning framework (DVC) uses these files to retrieve the artifacts from the artifact storage repository. 
