# Getting started with cmf-client

## cmf-client 

<font size=5>cmf-client is a tool that facilitates metadata collaboration between different teams or two team members. It allows users to pull or push metadata from or to the CMF server.</font>

## Setup a cmf-client
This section shows end-to-end setup of CMF Client.

### Pre-Requisites
- <p>Python 3.8+</p>
* <p>Git latest version</p>

### Install cmf library i.e. cmflib
```
pip install https://github.com/HewlettPackard/cmf
```
Check [HP cmf github](https://hewlettpackard.github.io/cmf/) for more details.

### Install cmf-server
cmf-server is a key interface for the user to explore and track their ML training runs. It allows users to store the metadata file on the cmf-server. The user can retrieve the saved metadata file and can view the content of the saved metadata file using the UI provided by the cmf-server.
Follow [cmf-server](https://github.com/varkha-d-sharma/cmf/blob/cmf_with_client_server/docs/cmf_server/cmf-server.md) for details on how to setup a cmf-server.</p>

## How to effectively use cmf-client?
The two most basic ways to use cmf-client are as follows:
- <p> Single User </p>
- <p> Two or more users </p>

Detailed description of the following commands is available on [Getting started with cmf-client commands](https://github.com/varkha-d-sharma/cmf/blob/cmf_with_client_server/docs/cmf_client/cmf_client.md).

### Single User
Assuming one single user is using a pipeline named "Test-env" with minio S3 bucket as the artifact repository and the same machine as the cmf-server.
#### Initialize CMF artifact repository
```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://127.0.0.1:80
```
#### Check status of CMF artifact initialization (Optional)
```
cmf init show
```
#### Track metadata using cmflib
Use [Sample projects](https://github.com/HewlettPackard/cmf/tree/master/examples) as a reference to create a new project to track metadata for ML pipelines.
More info is available on [HP cmf github examples](https://hewlettpackard.github.io/cmf/examples/getting_started/).
#### Push artifacts
```
cmf artifact push 
```
#### Push metadata to cmf-server.
```
cmf metadata push -p 'Test-env'
```
### Two or more Users
Assuming there are two users - User 1 and User 2. They are working on a common pipeline named "Test-env" with a common server and minio S3 bucket as the common artifact repository.

#### User 1 will follow the below mentioned steps
##### Initialize CMF artifact repository
```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://x.x.x.x:8080
```
##### Check status of CMF artifact initialization (Optional)
```
cmf init show
```
##### Track metadata using cmflib
Use [Sample projects](https://github.com/HewlettPackard/cmf/tree/master/examples) as a reference to create a new project to track metadata for ML pipelines.
More info is available on [HP cmf github examples](https://hewlettpackard.github.io/cmf/examples/getting_started/).
##### Push artifacts
```
cmf artifact push 
```
##### Push metadata to cmf-server.
```
cmf metadata push -p 'Test-env'
```

#### User 2 will follow the below mentioned steps
##### Initialize CMF artifact repository
```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://x.x.x.x:8080
```
##### Check status of CMF artifact initialization (Optional)
```
cmf init show
```
##### Pull metadata from common CMF server
```
cmf metadata pull -p "Test-env"
```
##### Pull artifacts from common artifact repo. 
```
cmf artifact pull -p "Test-env"
```
