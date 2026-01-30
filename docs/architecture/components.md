## CMFLib

The APIs and abstractions provided by CMFLib enable tracking of pipeline metadata. 

CMFLib tracks the stages in the pipeline, the input and output artifacts at each stage, and metrics. 

The framework allows metrics to be tracked at both coarse and fine-grained intervals. Stage metrics can be captured at the end of a stage, while fine-grained metrics can be tracked per step (epoch) or at regular intervals during the execution of the stage. 

The metadata logged through the APIs is written to a backend relational database. `CMFLib` also provides APIs to query the metadata stored in the relational database, allowing users to inspect pipelines.   

In addition to explicit tracking through the APIs, `CMFLib` provides implicit tracking. This automatically tracks the software version used in the pipelines.  

All artifacts are versioned using a data versioning framework (e.g., DVC). The content hash of the artifacts is generated and stored along with the user-provided metadata. A special artifact metadata file called a ".dvc" file is created for every artifact (file or folder) that is added to the data version management system. The .dvc file contains the content hash of the artifact.

For every pipeline, the metadata tracker creates a new branch to track the code. 

The special metadata file created for artifacts, “.dvc” file is too committed to Git, and its commit ID is tracked as a metadata information. Whenever there is a change in the artifact, the metadata file is modified to reflect its current content hash, and the file is tracked as a new version of the metadata file.  

The metadata tracker automatically tracks the start commit when CMFLib was initialized and creates a separate commit for each change in the artifact during the experiment. This helps to track the transformations of the artifacts across the different stages in the pipeline. 

## CMF Client 

The CMF Client interacts with the CMF Server for metadata synchronization.  

After the experiment is completed, the user invokes the `cmf push` command to push the collected metadata to the CMF Server. This transfers the existing metadata journal to the server.  

The metadata from the CMF Server can be pulled to the local repository using either artifacts or the project as the identifier, or both.

When an artifact is used as the identifier, all metadata associated with the artifacts currently present in the branch of the cloned Git repository is pulled from the central repository to the local repository. The pulled metadata consists of not only the immediate metadata associated with the artifacts, but also the metadata of all the artifacts in its chain of lineage. 

When a project is used as the identifier, all the metadata associated with the current branch of the pipeline code that is checked out is pulled to the local repository. 

## CMF Server 

The CMF Server exposes REST APIs that can be called from remote CMF Clients. 

In deployments with robust connectivity between the core datacenter and remote clients, the CMF Client can call the APIs exposed by the CMF Server to log metadata directly to the central metadata repository.

In scenarios where connectivity with the central server is intermittent, remote clients log the metadata to the local repository. The journaled metadata is then pushed by the remote client to the CMF Server. The central server replays the journal and merges the incoming metadata with the metadata already existing in the central repository. The ability to accurately identify artifacts anywhere using their content hash makes this merge operation robust and reliable.

## Central Repositories 

The Common Metadata Framework (CMF) consists of three central repositories for code, data, and metadata. 

### Central Metadata Repository

The central metadata repository holds the metadata pushed from distributed sites. It stores metadata about all the different pipelines that were tracked using the common metadata tracker. The consolidated view of the metadata stored in the central repository helps users learn across various stages of the pipeline executed at different locations. Using the query layer that points to the central repository, users get a global view of the metadata, which provides them with a deeper understanding of the pipelines and their metadata. The metadata helps to understand non-obvious results such as the performance of a dataset with respect to other datasets, or the performance of a particular pipeline with respect to other pipelines. 

### Central Artifact Storage Repository 

The central artifact storage repository stores all the artifacts related to experiments. The data versioning framework (DVC) stores the artifacts in a content-addressable layout. The artifacts are stored inside folders named with the first two characters of the content hash, and the artifact filename is the remaining part of the content hash. This layout enables efficient retrieval of artifacts.   

### Git Repository 

The Git repository is used to track the code. Along with the code, the metadata files of the artifacts (which contain the content hash of the artifacts) are also stored in Git. The data versioning framework (DVC) uses these files to retrieve the artifacts from the artifact storage repository. 
