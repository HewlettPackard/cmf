# Getting started with CMF Client commands

# cmf

```
Usage: cmf [-h] {init, artifact, metadata, execution, pipeline, repo, dvc}
```

The `cmf` command is a comprehensive tool designed to initialize an artifact repository and perform various operations on artifacts, execution, pipeline and metadata.

## cmf init

```
Usage: cmf init [-h] {local, minioS3, amazonS3, sshremote, osdfremote, show}
```

`cmf init` initializes an artifact repository for cmf. Local directory, Minio S3 bucket, Amazon S3 bucket, SSH Remote and Remote OSDF directory are the options available. Additionally, users can provide the CMF Server URL.

### cmf init show

```
Usage: cmf init show
```

`cmf init show` displays current cmf configuration.

### cmf init local

```
Usage: cmf init local [-h] --path [path]
                           --git-remote-url [git_remote_url]
                           --cmf-server-url [cmf_server_url]
                           --neo4j-user [neo4j_user]
                           --neo4j-password [neo4j_password]
                           --neo4j-uri [neo4j_uri]
```

`cmf init local` initialises local directory as a cmf artifact repository. Refer [local-storage-setup.md](./local-storage-setup.md) to set up a local storage.

**Basic Usage (Required Parameters Only):**
```
cmf init local --path /path/to/local-storage --git-remote-url https://github.com/user/experiment-repo.git
```

**With Optional Parameters:**
```
cmf init local --path /path/to/local-storage --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```

> **Note:** For `--path`, provide an absolute path to a directory outside of the current working directory which will serve as the artifact repository for artifacts across all CMF pipelines.

Required Arguments

```
  --path [path]                         Specify local directory path.
  --git-remote-url [git_remote_url]     Specify git repo url. eg: https://github.com/XXX/example.git
```

Optional Arguments

```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify CMF Server URL. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```

### cmf init minioS3

```
Usage: cmf init minioS3 [-h] --url [url]
                             --endpoint-url [endpoint_url]
                             --access-key-id [access_key_id]
                             --secret-key [secret_key]
                             --git-remote-url[git_remote_url]
                             --cmf-server-url [cmf_server_url]
                             --neo4j-user [neo4j_user]
                             --neo4j-password [neo4j_password]
                             --neo4j-uri [neo4j_uri]
```

`cmf init minioS3` configures Minio S3 bucket as a cmf artifact repository. Refer [minio-server.md](./minio-server.md#steps-to-set-up-a-minio-server) to set up a minio server.

**Basic Usage (Required Parameters Only):**
```
cmf init minioS3 --url s3://dvc-art --endpoint-url http://x.x.x.x:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git
```

**With Optional Parameters:**
```
cmf init minioS3 --url s3://dvc-art --endpoint-url http://x.x.x.x:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```

> Here, "dvc-art" is provided as an example bucket name. However, users can change it as needed, if the user chooses to change it, they will need to update the Dockerfile for MinIOS3 accordingly.

Required Arguments

```
  --url [url]                           Specify MinioS3 bucket url.
  --endpoint-url [endpoint_url]         Specify the endpoint url which is used to access Minio's locally/remotely running UI.
  --access-key-id [access_key_id]       Specify Access Key Id.
  --secret-key [secret_key]             Specify Secret Key.
  --git-remote-url [git_remote_url]     Specify git repo url. eg: https://github.com/XXX/example.git
```

Optional Arguments

```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify CMF Server URL. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```

### cmf init amazonS3

Before setting up, obtain AWS temporary security credentials using the AWS Security Token Service (STS). These credentials are short-term and can last from minutes to hours. They are dynamically generated and provided to trusted users upon request, and expire after use. Users with appropriate permissions can request new credentials before or upon expiration. For further information, refer to the [Temporary security credentials in IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html) page.

To retrieve temporary security credentials using multi-factor authentication (MFA) for an IAM user, you can use the below command.

```
aws sts get-session-token --duration-seconds <duration> --serial-number <MFA_device_serial_number> --token-code <MFA_token_code>
```

Required Arguments

```
  --serial-number                Specifies the serial number of the MFA device associated with the IAM user.
  --token-code                   Specifies the one-time code generated by the MFA device.
```

Optional Arguments

```
  --duration-seconds             Specifies the duration for which the temporary credentials will be valid, in seconds.
```

Example

```
aws sts get-session-token --duration-seconds 3600 --serial-number arn:aws:iam::123456789012:mfa/user --token-code 123456
```

This will return output like

```
{
    "Credentials": {
        "AccessKeyId": "ABCDEFGHIJKLMNO123456",
        "SecretAccessKey": "PQRSTUVWXYZ789101112131415",
        "SessionToken": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijlmnopqrstuvwxyz12345678910ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijlmnopqrstuvwxyz12345678910ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijlmnopqrstuvwxyz12345678910",
        "Expiration": "2021-05-10T15:31:08+00:00"
    }
}
```

Initialization of amazonS3

```
Usage: cmf init amazonS3 [-h] --url [url]
                              --access-key-id [access_key_id]
                              --secret-key [secret_key]
                              --session-token [session_token]
                              --git-remote-url [git_remote_url]
                              --cmf-server-url [cmf_server_url]
                              --neo4j-user [neo4j_user]
                              --neo4j-password [neo4j_password]
                              --neo4j-uri [neo4j_uri]
```

`cmf init amazonS3` initialises Amazon S3 bucket as a CMF artifact repository.

**Basic Usage (Required Parameters Only):**
```
cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --session-token XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git
```

**With Optional Parameters:**
```
cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --session-token XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```

> Here, use the --access-key-id, --secret-key and --session-token generated from the `aws sts` command which is mentioned above.

> The bucket-name must exist within Amazon S3 before executing the `cmf artifact push` command.

Required Arguments

```
  --url [url]                           Specify Amazon S3 bucket url.
  --access-key-id [access_key_id]       Specify Access Key Id.
  --secret-key [secret_key]             Specify Secret Key.
  --session-token                       Specify session token. (default: None)
  --git-remote-url [git_remote_url]     Specify git repo url. eg: https://github.com/XXX/example.git
```

Optional Arguments

```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify CMF Server URL. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```

### cmf init sshremote

```
Usage: cmf init sshremote [-h] --path [path]
                               --user [user]
                               --port [port]
                               --password [password]
                               --git-remote-url [git_remote_url]
                               --cmf-server-url [cmf_server_url]
                               --neo4j-user [neo4j_user]
                               --neo4j-password [neo4j_password]
                               --neo4j-uri [neo4j_uri]
```

`cmf init sshremote` command initialises remote ssh directory as a cmf artifact repository.

**Basic Usage (Required Parameters Only):**
```
cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git
```

**With Optional Parameters:**
```
cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://x.x.x.x:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```

Required Arguments

```
  --path [path]                           Specify remote ssh directory path.
  --user [user]                           Specify username.
  --port [port]                           Specify port.
  --password [password]                   Specify password. This will be saved only on local.
  --git-remote-url [git_remote_url]       Specify git repo url. eg: https://github.com/XXX/example.git
```

Optional Arguments

```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify CMF Server URL. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```

### cmf init osdfremote

```
Usage: cmf init osdfremote [-h] --path [path]
                             --cache [cache]
                             --key-id [key_id]
                             --key-path [key_path]
                             --key-issuer [key_issuer]
                             --git-remote-url[git_remote_url]
                             --cmf-server-url [cmf_server_url]
                             --neo4j-user [neo4j_user]
                             --neo4j-password [neo4j_password]
                             --neo4j-uri [neo4j_uri]
```

`cmf init osdfremote` configures a OSDF Origin as a cmf artifact repository.

**Basic Usage (Required Parameters Only):**
```
cmf init osdfremote --path https://[Some Origin]:8443/nrp/fdp/ --cache http://[Some Redirector] --key-id XXXX --key-path ~/.ssh/private.pem --key-issuer https://[Token Issuer] --git-remote-url https://github.com/user/experiment-repo.git
```

**With Optional Parameters:**
```
cmf init osdfremote --path https://[Some Origin]:8443/nrp/fdp/ --cache http://[Some Redirector] --key-id XXXX --key-path ~/.ssh/private.pem --key-issuer https://[Token Issuer] --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://127.0.0.1:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```

Required Arguments

```
  --path [path]                        Specify FQDN for OSDF origin including including port and directory path if any
  --cache                              Specify OSDF cache/director URL for retrieving data
  --key-id [key_id]                    Specify key_id for provided private key. eg. b2d3
  --key-path [key_path]                Specify path for private key on local filesystem. eg. ~/.ssh/XXX.pem
  --key-issuer [key_issuer]            Specify URL for Key Issuer. eg. https://t.nationalresearchplatform.org/XXX
  --git-remote-url [git_remote_url]    Specify git repo url. eg: https://github.com/XXX/example.git
```

Optional Arguments

```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify CMF Server URL. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri [neo4j_uri]             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)

```

## cmf metadata

```
Usage: cmf metadata [-h] {pull, push, export}
```

`cmf metadata` push, pull or export the metadata file to and from the CMF Server, respectively.

### cmf metadata pull

```
Usage: cmf metadata pull [-h] -p [pipeline_name] -f [file_name]  -e [exec_uuid]
```

`cmf metadata pull` command pulls the metadata file from the CMF Server to the user's local machine.

```
cmf metadata pull -p 'pipeline-name' -f '/path/to/mlmd-file-name' -e 'execution_uuid'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                                show this help message and exit.
  -e [exec_uuid], --execution_uuid [exec_uuid]              Specify execution uuid.
  -f [file_name], --file_name [file_name]                   Specify output metadata file name.
```

### cmf metadata push

```
Usage: cmf metadata push [-h] -p [pipeline_name] -f [file_name] -e [exec_uuid] -t [tensorboard_path]
```

`cmf metadata push` command pushes the metadata file from the local machine to the CMF Server.

```
cmf metadata push -p 'pipeline-name' -f '/path/to/mlmd-file-name' -e 'execution_uuid' -t '/path/to/tensorboard-log'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                                            show this help message and exit.
  -f [file_name], --file_name [file_name]                               Specify input metadata file name.
  -e [exec_uuid], --execution_uuid [exec_uuid]                          Specify execution uuid.
  -t [tensorboard_path], --tensorboard_path [tensorboard_path]          Specify path to tensorboard logs for the pipeline.
```

### cmf metadata export

```
Usage: cmf metadata export [-h] -p [pipeline_name] -j [json_file_name] -f [file_name]
```

`cmf metadata export` export local metadata's metadata in json format to a json file.

```
cmf metadata export -p 'pipeline-name' -j '/path/to/json-file-name' -f '/path/to/mlmd-file-name'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]        Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                               show this help message and exit.
  -f [file_name], --file_name [file_name]                  Specify the absolute or relative path for the input metadata file.
  -j [json_file_name], --json_file_name [json_file_name]   Specify output json file name with full path.
```


## cmf artifact

```
Usage: cmf artifact [-h] {pull, push, list}
```

`cmf artifact` pull, push or list artifacts from or to the user configured artifact repository, respectively.

### cmf artifact pull

```
Usage: cmf artifact pull [-h] -p [pipeline_name] -f [file_name] -a [artifact_name]
```

`cmf artifact pull` command pull artifacts from the user configured repository to the user's local machine.

```
cmf artifact pull -p 'pipeline-name' -f '/path/to/mlmd-file-name' -a 'artifact-name'
```

Required Arguments

```
  -p [pipeline_name], --pipeline-name [pipeline_name]   Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                            show this help message and exit.
  -a [artifact_name], --artifact_name [artifact_name]   Specify artifact name only (do not include folder path or absolute path).
  -f [file_name], --file_name [file_name]               Specify input metadata file name.
```

### cmf artifact push

```
Usage: cmf artifact push [-h] -p [pipeline_name] -f [file_name] -j [jobs]
```

`cmf artifact push` command push artifacts from the user's local machine to the user configured artifact repository.

```
cmf artifact push -p 'pipeline_name' -f '/path/to/mlmd-file-name' -j 'jobs'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]   Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                            show this help message and exit.
  -f [file_name], --file-name [file_name]               Specify mlmd file name.
  -j [jobs], --jobs [jobs]                              Number of parallel jobs for uploading artifacts to remote storage. Default is 4 * cpu_count().
                                                        Increasing jobs may speed up uploads but will use more resources.
```

### cmf artifact list

```
Usage: cmf artifact list [-h] -p [pipeline_name] -f [file_name] -a [artifact_name]
```

`cmf artifact list` command displays artifacts from the input metadata file with a few properties in a 7-column table, limited to 20 records per page.

```
cmf artifact list -p 'pipeline_name' -f '/path/to/mlmd-file-name' -a 'artifact_name'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]   Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                            show this help message and exit.
  -f [file_name], --file_name [file_name]               Specify input metadata file name.
  -a [artifact_name], --artifact_name [artifact_name]   Specify the artifact name to display detailed information about the given artifact name.
```

## cmf execution

```
Usage: cmf execution [-h] {list}
```

`cmf execution` command to displays executions from the metadata file.

### cmf execution list

```
Usage: cmf execution list [-h] -p [pipeline_name] -f [file_name] -e [execution_uuid]
```

`cmf execution list` command to displays executions from the input metadata file with a few properties in a 7-column table, limited to 20 records per page.

```
cmf execution list -p 'pipeline_name' -f '/path/to/mlmd-file-name' -e 'execution_uuid'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]       Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                                    show this help message and exit.
  --f [file_name], --file_name [file_name]                      Specify input metadata file name.
  -e [exec_uuid], --execution_uuid [exec_uuid]                  Specify the execution uuid to retrieve execution.
```

## cmf pipeline

```
Usage: cmf pipeline [-h] {list}
```

`cmf pipeline` command displays a list of pipeline name(s) from the available metadatafile.

### cmf pipeline list

```
Usage: cmf pipeline list [-h] -f [file_name]
```

`cmf pipeline list` command displays a list of pipeline name(s) from the available metadatafile.

```
cmf pipeline list -f '/path/to/mlmd-file-name'
```

Optional Arguments

```
  -h, --help                                            show this help message and exit.
  --f [file_name], --file_name [file_name]              Specify input metadata file name.
```

## cmf repo

```
Usage: cmf repo [-h] {push, pull}
```

`cmf repo` command push and pull artifacts, metadata files, and source code to and from the user's artifact repository, CMF Server, and Git respectively.

### cmf repo push

```
Usage: cmf repo push [-h] -p [pipeline_name] -f [file_name] -e [exec_uuid] -t [tensorboard] -j [jobs]
```

`cmf repo push` command push artifacts, metadata files, and source code to the user's artifact repository, CMF Server, and Git respectively.

```
cmf repo push -p 'pipeline-name' -f '/path/to/mlmd-file-name' -e 'execution_uuid' -t 'tensorboard_log_path' -j 'jobs'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]            Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                                     show this help message and exit.
  -f [file_name], --file-name [file_name]                        Specify mlmd file name.
  -e [exec_uuid], --execution_uuid [exec_uuid]                   Specify execution uuid.
  -t [tensorboard], --tensorboard [tensorboard]                  Specify path to tensorboard logs for the pipeline.
  -j [jobs], --jobs [jobs]                                       Number of parallel jobs for uploading artifacts to remote storage. Default is 4 * cpu_count().
                                                                 Increasing jobs may speed up uploads but will use more resources.
```

### cmf repo pull

```
Usage: cmf repo pull [-h] -p [pipeline_name] -f [file_name] -e [exec_uuid]
```

`cmf repo pull` command pull artifacts, metadata files, and source code from the user's artifact repository, CMF Server, and Git respectively.

```
cmf repo pull -p 'pipeline-name' -f '/path/to/mlmd-file-name' -e 'execution_uuid'
```

Required Arguments

```
  -p [pipeline_name], --pipeline_name [pipeline_name]            Specify Pipeline name.
```

Optional Arguments

```
  -h, --help                                                     show this help message and exit.
  -f [file_name], --file_name [file_name]                        Specify output metadata file name.
  -e [exec_uuid], --execution_uuid [exec_uuid]                   Specify execution uuid.
```

## cmf dvc

```
Usage: cmf dvc [-h] {ingest}
```

`cmf dvc` command ingests metadata from the dvc.lock file into CMF.

### cmf dvc ingest

```
Usage: cmf dvc ingest [-h] -f [file_name]
```

`cmf dvc ingest` command ingests metadata from the dvc.lock file into the CMF. If an existing MLMD file is provided, it merges and updates execution metadata based on matching commands, or creates new executions if none exist.

```
cmf dvc ingest -f '/path/to/mlmd-file-name'
```

Optional Arguments

```
  -h, --help                                                     show this help message and exit.
  -f [file_name], --file-name [file_name]                        Specify input mlmd file name. (default: mlmd)
```
