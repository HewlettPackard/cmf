# Architecture Overview

Interactions between different stages of a data pipelines are often challenging to track, particularly when artifacts
move bidirectionally between stages and/or when the stages themselves are executed on different platforms.
Additionally, each stage might have multiple dependencies, where the metadata and metrics produced by one stage
influence the execution of the remainder of the pipelines. Capturing the metadata across during the execution of
this pipeline is thus crucial to lineage tracking, provenance, and reproducibility.

The tracking of metadata through these complex pipelines have multiple challenges including

- Each stage in the pipeline could be executed in a different datacenter or an edge site having intermittent connection
  to the core datacenter
- Each stage in the pipeline could be managed by different teams
- The artifacts (input or output) need to be uniquely identified across different sites and across multiple pipelines.

Common metadata framework (CMF) addresses the problems associated with tracking of pipeline metadata from distributed
sites and tracks code, data and metadata together for end-to-end traceability.

The framework automatically tracks the code version as part of the execution of the pipeline's metadata. Additionally,
the data artifacts are also versioned automatically using a data versioning framework (like DVC) with data version
stored along with the code as metadata. The framework stores (1) the git commit id of the metadata file associated with
the artifact and (2) a hash of the artifact's content. The framework provides APIs to track the parameters and
other metadata of pipelines. From the metadata stored, users can zero in on the perparameters, code version and
the artifact version used for the experiment.

Identifying an artifact by its hash allows the framework to uniquely identify it on a distributed sites. These can
subsequently be merged to a central repository enabling a single source of truth for the global metadata across
multiple sites.

CMF thus provides a git-like experience for metadata, enabling users to push their local metadata to the
remote repository, where it is merged to create the global metadata and pull metadata from the global metadata to the
local, to create a local view, which would contain only the metadata of interest.

The framework can be used to track various types of data-oriented pipelines, for example data-processing or training
AI models.

<img src="./../../assets/framework.png" alt="CMF Framework" style="display: block; margin: 0 auto" />

