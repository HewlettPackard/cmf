# CMF Components
The Common Metadata Framework (CMF) has the following components:

- [Metadata Library](#metadata-library) exposes APIs to track pipeline metadata. It also provides APIs to query
  the stored metadata.
- [Local Client](#local-client) interacts with the server to pull or push metadata from or to the remote store.
- [Central Server](#central-server) interacts with all remote clients and is responsible for merging the metadata
  transferred by the remote client and managing the consolidated metadata.
- [Central Repositories](#central-repositories) host the code, data, and metadata.

<img src="../../assets/distributed_architecture.png" alt="CMF Framework" style="display: block; margin: 0 auto" />

## Metadata Library
The APIs and abstractions provided by CMF enable tracking of pipeline metadata. CMF tracks the stages in
the pipeline, the input and output artifacts at each stage, and potentially performance metrics (e.g., the value of the
loss function for a neural network). The framework allows metrics to be tracked at both coarse and fine-grained
intervals. For example, coarse-grained metrics of a stage are captured at the end of a stage. Fine-grained metrics
can be tracked per step (epoch) or at regular intervals during the execution of the stage.

The metadata logged through the APIs is written to a backend relational database. The library also provides APIs to
query the metadata stored in the relational database for users to inspect pipelines.

In addition to explicit tracking through the APIs, the library also provides implicit tracking, which automatically
tracks the software version used in the pipelines. The function arguments and function return values can
be automatically tracked by adding metadata tracker class decorators to the functions.

Before writing the metadata to the relational database, the metadata operations are recorded in the metadata journal log.
This enables the framework to transfer the local metadata to the central server.

All artifacts are versioned with a data versioning framework (e.g., DVC). The content hash of the artifacts is
generated and stored along with the user-provided metadata. A special artifact metadata file called a ``.dvc`` file is
created for every artifact (file/folder) that is added to the data version management system. The .dvc file contains the
content hash of the artifact.

For every new execution, the metadata tracker creates a new branch to track the code. The special metadata file created
for artifacts, the ``.dvc`` file, is committed to the directory and its commit ID is tracked as metadata information.
Artifacts themselves are versioned through the versioning of their metadata files. Whenever there is a change in an artifact,
the metadata file is modified to reflect its current content hash, and the file is tracked as a new version of the
metadata file.

The metadata tracker automatically tracks the start commit when the library is initialized and creates a separate commit
for each change in the artifact along the experiment. This helps to track the transformations of the artifacts along the
different stages in the pipeline.

## Local Client
The metadata client synchronizes the metadata with a remote server.

After the experiment is completed, the user invokes the ``cmf push`` command to push the collected metadata to the remote. 
This transfers the existing metadata journal to the server. The metadata from the central repository can also be pulled 
to the local repository, using either artifacts or the pipeline as the identifier.

When an artifact is used as the identifier, all metadata associated with the artifacts currently present in the branch of
the cloned git repository is pulled from the central repository to the local repository. The pulled metadata consists of
both the immediate metadata associated with the artifacts and the metadata of all the artifacts in its chain of lineage.

When a project is used as the identifier, all the metadata associated with the current branch of the pipeline code that
is checked out is pulled to the local repository.

## Central Server
The central server exposes REST APIs that can be called from remote clients. This is best for scenarios where the
core datacenter and the remote client have a strong, robust connection. In this case, the remote client calls the
APIs exposed by the central server to log the metadata directly to the central metadata repository.

Remote clients always log metadata locally. When the user initiates a push operation, the collected metadata is serialized 
as a JSON payload and sent to the central server. The server then stores the received metadata in the central repository. 
Direct logging of metadata from the client to the server is not supported; all metadata is first journaled locally and only 
transferred during a push.

## Central Repositories
The Common Metadata Framework consists of three central repositories for the code, data, and metadata.

#### Central Metadata Repository
The central metadata repository holds the metadata pushed from the distributed sites. It holds metadata about all the
different pipelines that were tracked using the common metadata tracker. The consolidated view of the metadata stored
in the central repository helps users browse the various stages in the pipeline executed at different
locations. Using the query layer that points to the central repository, the user gets a global view of the
metadata, providing them with a deeper understanding of the pipelines and their metadata. The metadata helps to
understand non-obvious results like the performance of a dataset with respect to other datasets, the performance of a particular
pipeline with respect to other pipelines, etc.

#### Central Artifact Storage Repository
The central artifact storage repository stores all the artifacts related to experiments. The data versioning framework (DVC)
stores the artifacts in a content-addressable layout. The artifacts are stored inside a folder with the name as the first
two characters of the content hash and the name of the artifact as the remaining part of the content hash. This helps
in efficient retrieval of the artifacts.

#### Git Repository
A Git repository is used to track the code. Along with the code, the metadata file of the artifacts, which contains the
content hash of the artifacts, is also tracked by git. The data versioning framework (DVC) uses these files to
retrieve the artifacts from the artifact storage repository.
