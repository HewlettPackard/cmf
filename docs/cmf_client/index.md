# Quick start with cmf-client
Common metadata framework (`cmf`) has the following components:

- **Metadata Library**: exposes APIs for tracking pipeline metadata and provides endpoints to query stored metadata.
- **cmf-client**: handles metadata exchange with the `cmf-server`, pushes and pulls artifacts from the artifact repository, and syncs code to and from GitHub.
- **cmf-server**: interacts with all the remote clients and is responsible for merging the metadata transferred by the `cmf-client` and manage the consolidated metadata.
- **Central Artifact Repositories**: host the code and data.

This tutorial walks you through the process of setting up the `cmf-client`.

## Prerequisites 
Before proceeding with the setup, ensure the following components are up and running:

- [cmflib](../setup/index.md/#install-cmf-library-ie-cmflib)
- [cmf-server](../setup/index.md/#install-cmf-server)

Make sure there are no errors during their startup, as cmf-client depends on both of these components.

## Setup a cmf-client
cmf-client is a command-line tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull or push metadata from or to the cmf-server.

Follow the below-mentioned steps for the end-to-end setup of cmf-client:-

**Configuration**

1. Create working directory `mkdir <workdir>`
2. Execute `cmf init` to configure the Data Version Control (DVC) remote directory, Git remote URL, CMF server, and Neo4j. Follow the [`cmf init`](./cmf_client_commands.md/#cmf-init) for more details.


## How to effectively use cmf-client?

Let's assume we are tracking the metadata for a pipeline named `Test-env` with a MinIO S3 bucket as the artifact repository and a cmf-server.

**Create a folder**
```
mkdir example-folder
```

### Initialize cmf

CMF initialization is the first and foremost step to use cmf-client commands. This command, in one go, completes the initialization process, making cmf-client user friendly. Execute `cmf init` in the `example-folder` directory created in the above step.
```
cmf init minioS3 --url s3://dvc-art --endpoint-url http://x.x.x.x:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:80  --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```
> Here, "dvc-art" is provided as an example bucket name. However, users can change it as needed. If the user chooses to change it, they will need to update the Dockerfile for minioS3 accordingly.

Check [cmf init minioS3](./cmf_client_commands.md/#cmf-init-minios3) for more details.

**Check status of CMF initialization (Optional)**
```
cmf init show
```
Check [cmf init show](./cmf_client.md/#cmf-init-show) for more details.

**Track metadata using cmflib**

Use [Sample projects](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/README.md) as a reference to create a new project to track metadata for ML pipelines.

More information is available inside [Getting Started Tutorial](../examples/getting_started.md).


> Before pushing artifacts or metadata, ensure that the cmf server and minioS3 are up and running.


**Push artifacts**

Push artifacts in the artifact repo initialized in the [Initialize cmf](#initialize-cmf) step.
```
cmf artifact push -p 'Test-env'
```
Check [cmf artifact push](./cmf_client_commands.md/#cmf-artifact-push) for more details.

**Push metadata to cmf-server**
```
cmf metadata push -p 'Test-env'
```
Check [cmf metadata push](./cmf_client_commands.md/#cmf-metadata-push) for more details.

### cmf-client with collaborative development
In the case of collaborative development, in addition to the above commands, users can follow the commands below to pull metadata and artifacts from a common cmf server and a central artifact repository.

**Pull metadata from the server**

Execute `cmf metadata pull` command in the `example_folder`.
```
cmf metadata pull -p 'Test-env'
```
Check [cmf metadata pull](./cmf_client_commands.md/#cmf-metadata-pull) for more details.

**Pull artifacts from the central artifact repo**

Execute `cmf artifact pull` command in the `example_folder`.
```
cmf artifact pull -p 'Test-env'
```
Check [cmf artifact pull](./cmf_client_commands.md/#cmf-artifact-pull) page for more details.

## Flow Chart for cmf
<img src="./../../assets/flow_chart_cmf.jpg" alt="Flow chart for cmf" style="display: block; margin: 0 auto" />
