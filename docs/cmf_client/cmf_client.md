# Getting started with cmf-client commands
## cmf init
<pre>
Usage: cmf init [-h] {minioS3,amazonS3,local,sshremote,show}
</pre>
**cmf init** initializes an artifact repository for CMF. Local directory, Minio S3 bucket, Amazon S3 bucket and SSH Remote directory are the options available. Additionally, user can provide cmf-server IP.

### cmf init show
<pre>
Usage: cmf init show
</pre>
**cmf init show** displays current cmf configuration.


### cmf init minioS3 
<pre>
Usage: cmf init minioS3 [-h] --url [url] --endpoint-url [endpoint_url]
                        --access-key-id [access_key_id] --secret-key [secret_key] --git-remote-url[git_remote_url]  --cmf-server-ip [cmf_server_ip]
</pre>
**cmf init minioS3** configures Minio S3 bucket as a CMF artifact repository. Refer [minio-server.md](./minio-server.md#steps-to-set-up-a-minio-server) to set up a minio server.

```
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://121.0.0.1:80
```
Required Arguments

<pre>
  --url [url]                           Specify bucket url.
  --endpoint-url [endpoint_url]         Specify the endpoint url of minio UI.
  --access-key-id [access_key_id]       Specify Access Key Id.
  --secret-key [secret_key]             Specify Secret Key.
  --git-remote-url [git_remote_url]     Specify git repo url.
</pre>

Optional Arguments

<pre>
  -h, --help  show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)
</pre>


### cmf init local
<pre>
Usage: cmf init local [-h] --path [path] --git-remote-url [git_remote_url] --cmf-server-ip [cmf_server_ip]
</pre>
**cmf init local** initialises local directory as a CMF artifact repository.

```
cmf init local --path /home/user/local-storage --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://121.0.0.1:80
```

Required Arguments

<pre>
  --path [path]                         Specify local directory path.
  --git-remote-url [git_remote_url]     Specify git repo url.
</pre>

Optional Arguments

<pre>
  -h, --help                        show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)
</pre>

### cmf init amazonS3
<pre>
Usage: cmf init amazonS3 [-h] --url [url] --access-key-id [access_key_id]
                         --secret-key [secret_key] --git-remote-url [git_remote_url] --cmf-server-ip [cmf_server_ip]
</pre>
**cmf init amazonS3** initialises Amazon S3 bucket as a CMF artifact repository.

```
cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://121.0.0.1:80
```

Required Arguments
<pre>
  --url [url]                           Specify bucket url.
  --access-key-id [access_key_id]       Specify Access Key Id.
  --secret-key [secret_key]             Specify Secret Key.
  --git-remote-url [git_remote_url]     Specify git repo url.
</pre>

Optional Arguments
<pre>
  -h, --help  show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)

</pre>

### cmf init sshremote
<pre>
Usage: cmf init sshremote [-h] --path [path] --user [user] --port [port]
                          --password [password]  --git-remote-url [git_remote_url] --cmf-server-ip [cmf_server_ip]
</pre>
**cmf init sshremote** command initialises remote ssh directory as a CMF artifact repository.
 
```
cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-ip http://121.0.0.1:80
```

Required Arguments

<pre>
  --path [path]                           Specify ssh directory path.
  --user [user]                           Specify user.
  --port [port]                           Specify Port.
  --password [password]                   Specify password.
  --git-remote-url [git_remote_url]       Specify git repo url.
</pre>

Optional Arguments
<pre>
  -h, --help  show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)
</pre>

## **cmf artifact**

<pre>
Usage: cmf artifact [-h] {pull,push}
</pre>
**cmf artifact** pull or push artifacts from or to the user configured artifact repository, respectively.
### cmf artifact pull
<pre>
Usage: cmf artifact pull [-h] -p [pipeline_name] -f [file_name]
</pre>
**cmf artifact pull** command pull artifacts from the user configured repository to the user's local machine.
```
cmf artifact pull -p 'Test-env'  
```

Required Arguments

<pre>
  -p [pipeline_name], --pipeline-name [pipeline_name]   Specify Pipeline name.

</pre>

Optional Arguments


<pre>
  -h, --help                                  show this help message and exit
  -f [file_name],--file-name [file_name]      Specify mlmd file name.
</pre>

### cmf artifact push
<pre>
Usage: cmf artifact push [-h] -p [pipeline_name] -f [file_name]
</pre>
**cmf artifact push** command push artifacts from the user's local machine to the user configured artifact repository.
```
cmf artifact push  
```

## cmf metadata

<pre>
Usage: cmf metadata [-h] {pull,push}
</pre>
**cmf metadata** push or pull the metadata file to and from the cmf-server, respectively.


### cmf metadata pull
<pre>
Usage: cmf metadata pull [-h] -p [pipeline_name] -f [file_path]  -e [exec_id]
</pre>
**cmf metadata pull** command pulls the metadata file from the cmf-server to the user's local machine.
```
cmf metadata pull -p 'Test-env' -f "/home/user/example/name_of_file"
```

Required Arguments

<pre>
  -p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name.
  -f [file_path], --file_path [file_path]                 Specify a location for mlmd file.

</pre>

Optional Arguments

<pre>
-h, --help                                  show this help message and exit
-e [exec_id], --execution [exec_name]       Specify execution id

</pre>

### cmf metadata push
<pre>
Usage: cmf metadata push [-h] -p [pipeline_name] -f [file_name]  -e [exec_id]
</pre>
**cmf metadata push** command pushes the metadata file from the local machine to the cmf-server.

```
cmf metadata push -p 'Test-env' -f "/home/user/example/name_of_file"
```

Required Arguments

<pre>
-p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name.
</pre>

Optional Arguments

<pre>
  -h, --help                                    show this help message and exit
  -f [file_name], --file_name [file_name]       Specify mlmd file name.
  -e [exec_name], --execution [exec_name]       Specify execution id.
</pre>









            




