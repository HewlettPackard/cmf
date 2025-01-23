# CMF Components
Common metadata framework has the following components:

- [Metadata Library](#metadata-library) exposes API’s to track the pipeline metadata. It also provides API’s to query
  the stored metadata.
- [Local Client](#local-client) interacts with the server to pull or push metadata from or to the remote store.
- [Central Server](#central-server) interacts with all the remote clients and is responsible to merge the metadata
  transferred by the remote client and manage the consolidated metadata.
- [Central Repositories](#central-repositories) hosts the code, data and metadata.

<img src="../../assets/distributed_architecture.png" alt="CMF Framework" style="display: block; margin: 0 auto" />


## Metadata Library
The APIs and the abstractions provided by the library enables tracking of pipeline metadata. CMF tracks the stages in
the pipeline, the input and output artifacts at each stage and metrics. The framework allows metrics to be tracked both
at coarse and fine-grained intervals. For example, coarse-grained metrics of stage are captured at the end of a stage.
Fine-grained metrics can be tracked per step (epoch) or at regular intervals during the execution of the stage

The metadata logged through the APIs are written to a backend relational database. The library also provides APIs to
query the metadata stored in the relational database for the users to inspect pipelines.

In addition to explicit tracking through the APIs, the library also provides implicit tracking which automatically
tracks the software version used in the pipelines. The function arguments and function return values can
be automatically tracked by adding metadata tracker class decorators on the functions.

Before writing the metadata to relational database, the metadata operations are journaled in the metadata journal log.
This enables the framework to transfer the local metadata to the central server.

All artifacts are versioned with a data versioning framework (e.g., DVC). The content hash of the artifacts are
generated and stored along with the user provided metadata. A special artifact metadata file called a ``.dvc`` file is
created for every artifact (file / folder) which is added to data version management system. The .dvc file contains the
content hash of the artifact.

For every new execution, the metadata tracker creates a new branch to track the code. The special metadata file created
for artifacts, the ``.dvc`` file is committed to the direcotry and its commit id is tracked as a metadata information.
Artifacts themsleves are versioned through the versioning of its metadata file. Whenever there is a change in the artifact,
the metadata file is modified to reflect its current content hash, and the file is tracked as a new version of the
metadata file.

The metadata tracker automatically tracks the start commit when the library was initialized and creates separate commit
for each change in the artifact along the experiment. This helps to track the transformations on the artifacts along the
different stages in the pipeline.

## Local Client
The metadata client interacts with the metadata server. It communicates with the server, for synchronization of metadata.

After the experiment is completed, the user invokes the ``cmf push`` command to push the collected metadata to the remote.
This transfers the existing metadata journal to the server.

The metadata from the central repository can be pulled to the local repository, either using the artifacts or using the
project as the identifier or both.

When artifact is used as the identifier, all metadata associated with the artifacts currently present in the branch of
the cloned Git repository is pulled from the central repository to the local repository. The pulled metadata consists of
both the immediate metadata associated with the artifacts and the metadata of all the artifacts in its chain of lineage.

When project is used as the identifier, all the metadata associated with the current branch of the pipeline code that
is checked out is pulled to the local repository.

## Central Server
The central server exposes REST APIs that can be called from the remote clients. This can help in situations where the
connectivity between the core datacenter and the remote client is robust. The remote client calls the API’s exposed by
the central server to log the metadata directly to the central metadata repository.

Where the connectivity with the central server is intermittent, the remote clients log the metadata to the local
repository. The journaled metadata is pushed by the remote client to the central server. The central server will
replay the journal and merge the incoming metadata with the metadata already existing in the central repository. The
ability to accurately identify the artifacts anywhere using their content hash, makes this merge robust.

## Central Repositories
The common metadata framework consist of three central repositories for the code, data and metadata.

#### Central Metadata repository
The central metadata repository holds the metadata pushed from the distributed sites. It holds metadata about all the
different pipelines that was tracked using the common metadata tracker. The consolidated view of the metadata stored
in the central repository helps the users browse the various stages in the pipeline executed at different
locations. Using the query layer that is pointed to the central repository, the user gets the global view of the
metadata providing them with a deeper understanding of the pipelines and its metadata.  The metadata helps to
understand nonobvious results like performance of a dataset with respect to other datasets, performance of a particular
pipeline with respect to other pipelines, etc.

#### Central Artifact storage repository
The Central Artifact storage repository stores all the artifacts related to experiment. The data versioning framework (DVC)
stores the artifacts in a content addressable layout. The artifacts are stored inside the folder with name as the first
two characters of the content hash and the name of the artifact as the remaining part of the content hash. This helps
in efficient retrieval of the artifacts.

#### Git Repository
Git repository is used to track the code. Along with the code, the metadata file of the artifacts which contain the
content hash of the artifacts are also tracked by git. The Data versioning framework (dvc) would use these files to
retrieve the artifacts from the artifact storage repository.
