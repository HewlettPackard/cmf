# Getting started with cmf
Common metadata framework (cmf) has the following components:

- **Metadata Library** exposes API’s to track the pipeline metadata. It also provides API’s to query the stored metadata. 
- **cmf-client** interacts with the server to pull or push metadata from or to the cmf-server.
- **cmf-server with GUI** interacts with all the remote clients and is responsible to merge the metadata transferred by the cmf-client and manage the consolidated metadata. GUI renders metadata for simplified tracking. 
- **Central Artifact Repositories** hosts the code and data. 

## Setup a cmf-client 
cmf-client is a tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull or push metadata from or to the cmf-server.

Follow the below-mentioned steps for the end-to-end setup of cmf-client:-

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
Check [here](https://hewlettpackard.github.io/cmf/) for more details.

## Install cmf-server
cmf-server is a key interface for the user to explore and track their ML training runs. It allows users to store the metadata file on the cmf-server. The user can retrieve the saved metadata file and can view the content of the saved metadata file using the UI provided by the cmf-server.

Follow [here](../cmf_server/cmf-server.md) for details on how to setup a cmf-server.

## How to effectively use cmf-client?

Let's assume we are tracking the metadata for a pipeline named `Test-env` with minio S3 bucket as the artifact repository and a cmf-server.

**Create a folder**
```
mkdir example-folder
```
  
**Initialize cmf**

CMF initialization is the first and foremost to use cmf-client commads. This command in one go complete initialization process making cmf-client user friendly.     Execute `cmf init` in the `example-folder` directory created in the [above](#create-a-folder) step.
```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:8080  --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://X.X.X.X:7687
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
  
Push artifacts in the artifact repo initialised in the [Initialize cmf](#initialize-cmf) step.
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
