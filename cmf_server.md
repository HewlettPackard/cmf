## CMF Commands

### 1. cmf artifact
<pre>
Usage: cmf artifact [-h] {pull,push}
</pre>
This command pulls and pushes artifacts to minio server.
###     cmf artifact pull
<pre>
Usage: cmf artifact pull [-h] -p <pipeline_name> [-f <file_name>]
</pre>
This command pulls artifacts from minio s3 bucket to local

Returns ?

| Arguments     |                         |
|---------------|-------------------------|
| Filename      | Specify mlmd file name  | 
| Pipeline name | Specify pipeline name   |
| Help          | show this help and exit |

###     cmf artifact push
<pre>
Usage: cmf artifact push [-h] -p pipeline_name [-f file_name]
</pre>
This command pushes artifacts from local to minio s3 bucket 

### 2. cmf metadata
<pre>
Usage: cmf metadata [-h] {pull,push}
</pre>
This command pulls and pushes artifacts to minio server.
###     cmf metadata pull
<pre>
Usage: cmf metadata pull [-h] -p pipeline_name [-f file_name]  [-e exec_name]
</pre>
This command pulls mlmd file from server to local

Returns ?

| Arguments     |                                                    |
|---------------|----------------------------------------------------|
| Filepath      | Specify path to pull mlmd file                     | 
| Pipeline name | Specify pipeline name                              |
| Execution ID  | Specify execution id to execution from mlmd server |
| Help          | show this help and exit |

###     cmf metadata push
<pre>
Usage: cmf metadata push [-h] -p pipeline_name [-f file_name]  [-e exec_name]
</pre>
This command pushes metadata mlmd name from local to minio s3 bucket 

Returns ?

| Arguments     |                                                    |
|---------------|----------------------------------------------------|
| Filepath      | Specify path to get mlmd file to push to server    | 
| Pipeline name | Specify pipeline name                              |
| Execution ID  | Specify execution id to execution from mlmd server |
| Help          | show this help and exit |

### 2. cmf init
<pre>
Usage: cmf init [-h] {pull,push}
</pre>
This command is used initialize CMF for multiple repos

###     cmf init
<pre>
usage: cmf init [-h] {minioremote,amazonS3,local,sshremote}
</pre>
This command pulls mlmd file from server to local

Returns ?

| Arguments     |                                                    |
|---------------|----------------------------------------------------|
| Filepath      | Specify path to pull mlmd file                     | 
| Pipeline name | Specify pipeline name                              |
| Execution ID  | Specify execution id to execution from mlmd server |
| Help          | show this help and exit |

###     cmf init
<pre>
usage: cmf init minioremote [-h] --url <url> --endpoint-url <endpoint_url> --access-key-id <access_key_id> --secret-key <secret_key>
</pre>
This is command is to initialize minio S3 bucket

Returns ?

| Arguments    |                                                     |
|--------------|-----------------------------------------------------|
| url          | Specify url to bucket                               | 
| Endpoint url | Specify endpoint url which is used to access minio  locally/remotely running UI |
| access_key_id | Specify Access Key Id  |
|secret_key|Specify Secret Key|
| Help         | show this help and exit                             |











            



#