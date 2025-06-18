# Quick start with cmf-client
Common metadata framework (cmf) has the following components:

- **Metadata Library** exposes APIs to track the pipeline metadata. It also provides APIs to query the stored metadata.
- **cmf-client** interacts with the server to pull or push metadata from or to the cmf-server.
- **cmf-server** interacts with all the remote clients and is responsible for merging the metadata transferred by the `cmf-client` and managing the consolidated metadata.
- **Central Artifact Repositories** host the code and data.

## Install cmf library i.e. cmflib
Before proceeding, ensure that the CMF library is installed on your system. If not, follow the installation instructions provided inside the [CMF in a nutshell](../index.md) page.

## Install cmf-server
cmf-server is a key interface for the user to explore and track their ML training runs. It allows users to store the metadata file on the cmf-server. The user can retrieve the saved metadata file and can view the content of the saved metadata file using the UI provided by the cmf-server.

Follow the instructions on the [Getting started with cmf-server](../cmf_server/cmf-server.md) page for details on how to setup a cmf-server.

## Setup a cmf-client
cmf-client is a tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull or push metadata from or to the cmf-server.

Follow the below-mentioned steps for the end-to-end setup of cmf-client:-

**Configuration**

1. Create working directory `mkdir <workdir>`
2. Execute `cmf init` to configure the Data Version Control (DVC) remote directory, Git remote URL, CMF server, and Neo4j. Follow the [Overview](./cmf_client.md) page for more details.



## How to effectively use cmf-client?

Let's assume we are tracking the metadata for a pipeline named `Test-env` with a MinIO S3 bucket as the artifact repository and a cmf-server.

**Create a folder**
```
mkdir example-folder
```

**Initialize cmf**

CMF initialization is the first and foremost step to use cmf-client commands. This command, in one go, completes the initialization process, making cmf-client user friendly. Execute `cmf init` in the `example-folder` directory created in the above step.
```
cmf init minioS3 --url s3://dvc-art --endpoint-url http://x.x.x.x:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:8080  --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```
> Here, "dvc-art" is provided as an example bucket name. However, users can change it as needed. If the user chooses to change it, they will need to update the Dockerfile for minioS3 accordingly.

Check [Overview](./cmf_client.md) page for more details.

**Check status of CMF initialization (Optional)**
```
cmf init show
```
Check [Overview](./cmf_client.md) page for more details.

**Track metadata using cmflib**

Use [Sample projects](https://github.com/HewlettPackard/cmf/blob/master/examples/example-get-started/README.md) as a reference to create a new project to track metadata for ML pipelines.

More information is available inside [Getting Started](https://hewlettpackard.github.io/cmf/examples/getting_started/).


> Before pushing artifacts or metadata, ensure that the cmf server and minioS3 are up and running.


**Push artifacts**

Push artifacts in the artifact repo initialized in the [Initialize cmf](#initialize-cmf) step.
```
cmf artifact push -p 'Test-env'
```
Check [Overview](./cmf_client.md) page for more details.

**Push metadata to cmf-server**
```
cmf metadata push -p 'Test-env'
```
Check [Overview](./cmf_client.md) page for more details.

### cmf-client with collaborative development
In the case of collaborative development, in addition to the above commands, users can follow the commands below to pull metadata and artifacts from a common cmf server and a central artifact repository.

**Pull metadata from the server**

Execute `cmf metadata` command in the `example_folder`.
```
cmf metadata pull -p 'Test-env'
```
Check [Overview](./cmf_client.md) page for more details.

**Pull artifacts from the central artifact repo**

Execute `cmf artifact` command in the `example_folder`.
```
cmf artifact pull -p 'Test-env'
```
Check [Overview](./cmf_client.md) page for more details.

## Flow Chart for cmf
<img src="./../../assets/flow_chart_cmf.jpg" alt="Flow chart for cmf" style="display: block; margin: 0 auto" />
