# Getting started with cmf
Common Metadata Framework (CMF) has the following components:

- **Metadata Library** exposes APIs to track pipeline metadata. It also provides APIs to query the stored metadata.
- **cmf-client** interacts with the cmf-server to pull or push metadata.
- **cmf-server with GUI** interacts with remote cmf-clients and merges the metadata transferred by each
  client. This server also provides a GUI that can render the stored metadata.
- **Central Artifact Repositories** host the code and data.

## Setup a cmf-client
`cmf-client` is a tool that facilitates metadata collaboration between different teams and team members. These clients
interact with the cmf-server to push/pull metadata.

**Pre-Requisites**

- Python 3.9+
- Git latest version

**Install cmf library i.e. cmflib**
```
pip install https://github.com/HewlettPackard/cmf
```
**OR**
```
pip install cmflib
```
[Documentation](https://hewlettpackard.github.io/cmf/) for more details.

## Install cmf-server
cmf-server is the primary interface for the user to explore and track their ML training runs by browsing the stored
metadata. Users can retrieve the saved metadata file and can view the content of the saved metadata file using
the UI provided by the cmf-server.

Details on how to set up a cmf-server can be found [here](../cmf_server/cmf-server.md).

## Simple Example of using the CMF Client
In this example, CMF is used to track the metadata for a pipeline named `Test-env` which interacts with a MinIO

S3 bucket as the artifact repository and a cmf-server.

**Setup the example directory**
```
mkdir example-folder && cd example-folder
```

**Initialize cmf**

CMF must be initialized to use cmf-client commands. The following command configures authentication to an S3 bucket and
specifies the connection to a CMF server.
```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 \
  --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git \
  --cmf-server-url http://x.x.x.x:8080  --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://X.X.X.X:7687
```
Check [here](./cmf_client.md) for more details.

**Check status of CMF initialization (Optional)**
```
cmf init show
```
Check [here](./cmf_client.md) for more details.

**Track metadata using cmflib**

Use [Sample projects](https://github.com/HewlettPackard/cmf/tree/master/examples) as a reference to create a new project to track metadata for ML pipelines.

More info is available [here](https://hewlettpackard.github.io/cmf/examples/getting_started/).

**Push artifacts**

Push artifacts in the artifact repo initialized in the [Initialize cmf](#initialize-cmf) step.
```
cmf artifact push
```
Check [here](./cmf_client.md) for more details.

**Push metadata to cmf-server**
```
cmf metadata push -p 'Test-env'
```
Check [here](./cmf_client.md) for more details.

### cmf-client with collaborative development
In the case of collaborative development, in addition to the above commands, users can follow the commands below to pull metadata and artifacts from a common cmf server and a central artifact repository.

**Pull metadata from the server**

Execute `cmf metadata` command in the `example_folder`.
```
cmf metadata pull -p 'Test-env'
```
Check [here](./cmf_client.md) for more details.

**Pull artifacts from the central artifact repo**

Execute `cmf artifact` command in the `example_folder`.
```
cmf artifact pull -p "Test-env"
```
Check [here](./cmf_client.md) for more details.

## Flow Chart for cmf
<img src="./../assets/flow_chart_cmf.jpg" alt="Flow chart for cmf" style="display: block; margin: 0 auto" />
