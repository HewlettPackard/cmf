# Architecture Overview

**Common Metadata Framework (CMF)** implements a system for collecting, storing, and querying metadata associated with Machine Learning (ML) pipelines. 

CMF adopts a data-first approach where all artifacts (datasets, ML models, and performance metrics) are versioned and identified by their content hash, enabling distributed metadata tracking and collaboration across ML teams.

CMF collects and stores information associated with Machine Learning (ML) pipelines. It also implements APIs to query this metadata. The CMF adopts a data-first approach: all artifacts (such as datasets, ML models and performance metrics) recorded by the framework are versioned and identified by their content hash.

Interactions in data pipelines can be complex. The Different stages in the pipeline, (which may not be next to each other) may have to interact to produce or transform artifacts. As the artifacts navigates and undergo transformations through this pipeline, it can take a complicated path, which might also involve bidirectional movement across these stages.  Also there could be dependencies between the multiple stages, where the metrics produced by a stage could influence the metrics at a subsequent stage.  It is important to track the metadata across a pipeline to provide features like, lineage tracking, provenance and reproducibility.  

The tracking of metadata through these complex pipelines have multiple challenges, some of them being,  

- Each stage in the pipeline could be executed in a different datacenter or an edge site having intermittent connection to the core datacenter.   
- Each stage in the pipeline could be possibly managed by different teams.  
- The artifacts (input or output) needs to be uniquely identified across different sites and across multiple pipelines. 


Common metadata framework (CMF) addresses the problems associated with tracking of pipeline metadata from distributed sites and tracks code, data and metadata together for end-to-end traceability.   

The framework automatically tracks the code version as one of the metadata for an execution. Additionally the data artifacts are also versioned automatically using a data versioning framework (like DVC) and the metadata regarding the data version is stored along with the code. The framework stores the Git commit id of the metadata file associated with the artifact and content hash of the artifact as metadata. The framework provides API’s to track the hyper parameters and other metadata of pipelines.  Therefore from the metadata stored, users can zero in on the hyper parameters, code version and the artifact version used for the experiment. 

Identifying the artifacts by content hash allows the framework, to uniquely identify an artifact anywhere in the distributed sites. This enables the metadata from the distributed sites to be precisely merged to a central repository, thereby providing a single global metadata from the distributed sites.   

On this backbone, we build the Git like experience for metadata, enabling users to push their local metadata to the remote repository, where it is merged to create the global metadata and pull metadata from the global metadata to the local, to create a local view, which would contain only the metadata of interest. 

The framework can be used to track various types of pipelines such as data pipelines or AI pipelines. 
<p align="center">
 <img src="../../assets/framework.png" height="400" align="center" />
</p>

