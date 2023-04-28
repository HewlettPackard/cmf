# Getting started with cmf-client commands
## cmf init
```
Usage: cmf init [-h] {minioS3,amazonS3,local,sshremote,show}
```
`cmf init` initializes an artifact repository for cmf. Local directory, Minio S3 bucket, Amazon S3 bucket and SSH Remote directory are the options available. Additionally, user can provide cmf-server url.
### cmf init show
```
Usage: cmf init show
```
`cmf init show` displays current cmf configuration.

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
```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://127.0.0.1:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```
Required Arguments
```
  --url [url]                           Specify bucket url.
  --endpoint-url [endpoint_url]         Specify the endpoint url of minio UI.
  --access-key-id [access_key_id]       Specify Access Key Id.
  --secret-key [secret_key]             Specify Secret Key.
  --git-remote-url [git_remote_url]     Specify git repo url.
```
Optional Arguments
```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify cmf-server url. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri <neo4j_uri>             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
                        

```
### cmf init local
```
Usage: cmf init local [-h] --path [path] -
                           --git-remote-url [git_remote_url]
                           --cmf-server-url [cmf_server_url]
                           --neo4j-user [neo4j_user]
                           --neo4j-password [neo4j_password]
                           --neo4j-uri [neo4j_uri]
```
`cmf init local` initialises local directory as a cmf artifact repository.
```
cmf init local --path /home/user/local-storage --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://127.0.0.1:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```
Required Arguments
```
  --path [path]                         Specify local directory path.
  --git-remote-url [git_remote_url]     Specify git repo url.
```
Optional Arguments
```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify cmf-server url. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri <neo4j_uri>             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```
### cmf init amazonS3
```
Usage: cmf init amazonS3 [-h] --url [url] 
                              --access-key-id [access_key_id]
                              --secret-key [secret_key] 
                              --git-remote-url [git_remote_url] 
                              --cmf-server-url [cmf_server_url]
                              --neo4j-user [neo4j_user]
                              --neo4j-password neo4j_password]
                              --neo4j-uri [neo4j_uri]
```
`cmf init amazonS3` initialises Amazon S3 bucket as a CMF artifact repository.
```
cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://127.0.0.1:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687 
```

Required Arguments
```
  --url [url]                           Specify bucket url.
  --access-key-id [access_key_id]       Specify Access Key Id.
  --secret-key [secret_key]             Specify Secret Key.
  --git-remote-url [git_remote_url]     Specify git repo url.
```
Optional Arguments
```
  -h, --help                          show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify cmf-server url. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri <neo4j_uri>             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```
### cmf init sshremote
```
Usage: cmf init sshremote [-h] --path [path] 
                               --user [user] --port [port]
                               --password [password]  
                               --git-remote-url [git_remote_url] 
                               --cmf-server-url [cmf_server_url]
                               --neo4j-user [neo4j_user]
                              --neo4j-password neo4j_password]
                              --neo4j-uri [neo4j_uri]
```
`cmf init sshremote` command initialises remote ssh directory as a cmf artifact repository.
```
cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://127.0.0.1:80 --neo4j-user neo4j --neo4j-password password --neo4j-uri bolt://localhost:7687
```
Required Arguments
```
  --path [path]                           Specify ssh directory path.
  --user [user]                           Specify user.
  --port [port]                           Specify Port.
  --password [password]                   Specify password.
  --git-remote-url [git_remote_url]       Specify git repo url.
```
Optional Arguments
```
  -h, --help  show this help message and exit
  --cmf-server-url [cmf_server_url]   Specify cmf-server url. (default: http://127.0.0.1:80)
  --neo4j-user [neo4j_user]           Specify neo4j user. (default: None)
  --neo4j-password [neo4j_password]   Specify neo4j password. (default: None)
  --neo4j-uri <neo4j_uri>             Specify neo4j uri. Eg bolt://localhost:7687 (default: None)
```

## cmf artifact
```
Usage: cmf artifact [-h] {pull,push}
```
`cmf artifact` pull or push artifacts from or to the user configured artifact repository, respectively.
### cmf artifact pull
```
Usage: cmf artifact pull [-h] -p [pipeline_name] -f [file_name]
```
`cmf artifact pull` command pull artifacts from the user configured repository to the user's local machine.
```
cmf artifact pull -p 'Test-env'  
```
Required Arguments
```
  -p [pipeline_name], --pipeline-name [pipeline_name]   Specify Pipeline name.
```
Optional Arguments
```
  -h, --help                                  show this help message and exit
  -f [file_name],--file-name [file_name]      Specify mlmd file name.
```
### cmf artifact push
```
Usage: cmf artifact push [-h] -p [pipeline_name] -f [file_name]
```
`cmf artifact push` command push artifacts from the user's local machine to the user configured artifact repository.
```
cmf artifact push  
```
## cmf metadata
```
Usage: cmf metadata [-h] {pull,push}
```
`cmf metadata` push or pull the metadata file to and from the cmf-server, respectively.
### cmf metadata pull
```
Usage: cmf metadata pull [-h] -p [pipeline_name] -f [file_path]  -e [exec_id]
```
`cmf metadata pull` command pulls the metadata file from the cmf-server to the user's local machine.
```
cmf metadata pull -p 'Test-env' -f "/home/user/example/name_of_file"
```
Required Arguments
```
  -p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name.
  -f [file_path], --file_path [file_path]                 Specify a location for mlmd file.
```
Optional Arguments
```
-h, --help                                  show this help message and exit
-e [exec_id], --execution [exec_name]       Specify execution id
```
### cmf metadata push
```
Usage: cmf metadata push [-h] -p [pipeline_name] -f [file_name]  -e [exec_id]
```
`cmf metadata push` command pushes the metadata file from the local machine to the cmf-server.
```
cmf metadata push -p 'Test-env' -f "/home/user/example/name_of_file"
```
Required Arguments
```
-p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name.
```

Optional Arguments
```
  -h, --help                                    show this help message and exit
  -f [file_name], --file_name [file_name]       Specify mlmd file name.
  -e [exec_name], --execution [exec_name]       Specify execution id.
```
