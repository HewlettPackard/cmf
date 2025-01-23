# Architecture Overview

Interactions in data pipelines can be complex. The different stages in the pipeline, (which may not be next to each
other, AES: what does this mean?) may have to interact to produce or transform artifacts. As the artifacts flow through
and undergo transformations
through this pipeline, it can take a complicated path, which might also involve bidirectional movement across these
stages.
Additionally, these stages can have multipled dependencies, where the metrics produced by one stage could influence the
metrics at a subsequent stage.  Tracking the metadata across a pipeline is thus crucial to lineage tracking, provenance
and reproducibility.

The tracking of metadata through these complex pipelines have multiple challenges including

- Each stage in the pipeline could be executed in a different datacenter or an edge site having intermittent connection
  to the core datacenter
- Each stage in the pipeline could be possibly managed by different teams
- The artifacts (input or output) needs to be uniquely identified across different sites and across multiple pipelines.

Common metadata framework (CMF) addresses the problems associated with tracking of pipeline metadata from distributed
sites and tracks code, data and metadata together for end-to-end traceability.

The framework automatically tracks the code version as one of the metadata for an execution. Additionally, the data
artifacts are also versioned automatically using a data versioning framework (like DVC) and the metadata regarding the
data version is stored along with the code. The framework stores the git commit id of the metadata file associated with
the artifact and content hash of the artifact as metadata. The framework provides APIs to track the hyperparameters and
other metadata of pipelines.  Therefore, from the metadata stored, users can zero in on the hyperparameters, code
version and the artifact version used for the experiment.

Identifying the artifacts by content hash allows the framework, to uniquely identify an artifact anywhere in the
distributed sites. This enables the metadata from the distributed sites to be precisely merged to a central repository,
thereby providing a single global metadata from the distributed sites.

On this backbone, we build a git-like experience for metadata, enabling users to push their local metadata to the
remote repository, where it is merged to create the global metadata and pull metadata from the global metadata to the
local, to create a local view, which would contain only the metadata of interest.

The framework can be used to track various types of pipelines such as data pipelines or AI pipelines.

<img src="./../../assets/framework.png" alt="CMF Framework" style="display: block; margin: 0 auto" />

