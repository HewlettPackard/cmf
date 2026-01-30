## Quick start with CMF Client
Common Metadata Framework (`CMF`) has the following components:

- **CMFLib**: A Python library that captures and tracks metadata throughout your ML pipeline, including datasets, models, and metrics. It provides APIs for both logging metadata during execution and querying it later for analysis.
- **CMF Client**: A command-line tool that synchronizes metadata with the `CMF Server`, manages artifact transfers to and from storage repositories, and integrates with Git for version control.
- **CMF Server with GUI**: A centralized server that aggregates metadata from multiple clients and provides a web-based graphical interface for visualizing pipeline executions, artifacts, and lineage relationships, enabling teams to collaborate effectively.
- **Central Artifact Repositories**: Storage backends (such as AWS S3, MinIO, or SSH-based storage) that host your datasets, models, and other pipeline artifacts.

This tutorial walks you through the process of setting up the `CMF Client`.

## Prerequisites 
Before proceeding with the setup, ensure the following components are up and running:

- [CMFLib](../setup/index.md#install-cmf-library-ie-cmflib)
- [CMF Server](../setup/index.md#install-cmf-server-with-gui)

Make sure there are no errors during their startup, as `CMF Client` depends on both of these components.

## Setup a `CMF Client`
`CMF Client` is a command-line tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull or push metadata from or to the `CMF Server`.

Follow the below-mentioned steps for the end-to-end setup of `CMF Client`:-

**Configuration**

1. Create working directory `mkdir <workdir>`
2. Execute `cmf init` to configure the Data Version Control (DVC) remote directory, Git remote URL, CMF server, and Neo4j. Follow the [`cmf init`](./cmf_client_commands.md#cmf-init) for more details.


## How to effectively use CMF Client?

Let's assume we are tracking the metadata for a pipeline named `Test-env` with a MinIO S3 bucket as the artifact repository and a CMF Server.

**Create a folder**
```
mkdir example-folder
```

### Initialize cmf

CMF initialization is the first and foremost step to use CMF Client commands. This command completes the initialization process in one step, making the CMF Client user-friendly. Execute `cmf init` in the `example-folder` directory created in the above step.
```
cmf init minioS3 --url s3://dvc-art
                 --endpoint-url http://x.x.x.x:9000
                 --access-key-id minioadmin
                 --secret-key minioadmin
                 --git-remote-url https://github.com/user/experiment-repo.git
                 --cmf-server-url http://x.x.x.x:80
                 --neo4j-user neo4j
                 --neo4j-password password
                 --neo4j-uri bolt://localhost:7687
```
> Here, "dvc-art" is provided as an example bucket name. However, users can change it as needed. If the user chooses to change it, they will need to update the Dockerfile for minioS3 accordingly.

Check [cmf init minioS3](./cmf_client_commands.md#cmf-init-minios3) for more details.

**Check status of CMF initialization (Optional)**
```
cmf init show
```
Check [cmf init show](./cmf_client_commands.md#cmf-init-show) for more details.

**Track metadata using CMFLib**

Use [Sample projects](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/README.md) as a reference to create a new project to track metadata for ML pipelines.

More information is available inside [Getting Started Tutorial](../examples/getting_started.md).


> Before pushing artifacts or metadata, ensure that the CMF Server and minioS3 are up and running.


**Push artifacts**

Push artifacts in the artifact repository initialized in the [Initialize cmf](#initialize-cmf) step.
```
cmf artifact push -p 'Test-env'
```
Check [cmf artifact push](./cmf_client_commands.md#cmf-artifact-push) for more details.

**Push metadata to CMF Server**
```
cmf metadata push -p 'Test-env'
```
Check [cmf metadata push](./cmf_client_commands.md#cmf-metadata-push) for more details.

### CMF Client with collaborative development
In the case of collaborative development, in addition to the above commands, users can follow the commands below to pull metadata and artifacts from a common CMF Server and a central artifact repository.

**Pull metadata from the server**

Execute `cmf metadata pull` command in the `example_folder`.
```
cmf metadata pull -p 'Test-env'
```
Check [cmf metadata pull](./cmf_client_commands.md#cmf-metadata-pull) for more details.

**Pull artifacts from the central artifact repository**

Execute `cmf artifact pull` command in the `example_folder`.
```
cmf artifact pull -p 'Test-env'
```
Check [cmf artifact pull](./cmf_client_commands.md#cmf-artifact-pull) page for more details.

## Flow Chart for cmf
<img src="./../assets/flow_chart_cmf.jpg" alt="Flow chart for cmf" style="display: block; margin: 0 auto" />
`CMF Client` is a command-line tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull/push metadata from or to the `CMF Server` with similar functionalities for artifact repositories and other commands.
