## Getting started with CMF Commands
## <font size=6>**cmf init**</font> 

<pre>
Usage: cmf init [-h] {minioS3,amazonS3,local,sshremote,show}
</pre>
<font size=5> Initializes different repos for CMF such as local directories, Minio S3 bucket, Amazon S3 bucket, SSH Remote directories. Additionally, User can provide cmf-server IP. </font>

***
### 1.    cmf init show
<pre>
Usage: cmf init show
</pre>
<font size=5> Shows current cmf configuration.</font>

***

### 2. cmf init minioS3 
<pre>
Usage: cmf init minioS3 [-h] --url [url] --endpoint-url [endpoint_url]
                        --access-key-id [access_key_id] --secret-key [secret_key] --git-remote-url[git_remote_url]
</pre>
<font size=5> This command configures Minio S3 client machine.</font>

<pre>

Example:
cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git
</pre>

<font size=5> Required Arguments</font>

<pre>
  --url [url]                           Specify the url to bucket
  --endpoint-url [endpoint_url]         Specify the endpoint url which is used to access minio locally/remotely running UI
  --access-key-id [access_key_id]       Specify Access Key Id
  --secret-key [secret_key]             Specify Secret Key
  --git-remote-url [git_remote_url]     Url to git repo
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help  show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)
</pre>




***
### 3.    cmf init local
<pre>
Usage: cmf init local [-h] --path [path] --git-remote-url [git_remote_url]
</pre>
<font size=5> This command is used to initialise local bucket. </font>

<pre>
Example: 
cmf init local --path /home/user/local-storage --git-remote-url https://github.com/user/experiment-repo.git
</pre>

<font size=5> Required Arguments</font>

<pre>
  --path [path]                         Specify the url to bucket.
  --git-remote-url [git_remote_url]     Url to git repo
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help                        show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)
</pre>
***
### 4.    cmf init amazonS3
<pre>
Usage: cmf init amazonS3 [-h] --url [url] --access-key-id [access_key_id]
                         --secret-key [secret_key] --git-remote-url [git_remote_url]
</pre>
<font size=5> This command is used to initialise Amazon S3 bucket. </font>
 
<pre>
Example:
cmf init amazonS3 --url s3://bucket-name --access-key-id XXXXXXXXXXXXX --secret-key XXXXXXXXXXXXX --git-remote-url https://github.com/user/experiment-repo.git
</pre>

<font size=5> Required Arguments</font>
<pre>
  --url [url]                           Specify the url to the bucket
  --access-key-id [access_key_id]       Specify Access Key Id
  --secret-key [secret_key]             Specify Secret Key
  --git-remote-url [git_remote_url]     Url to git repo
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help  show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)

</pre>

***
### 5.    cmf init sshremote
<pre>
Usage: cmf init sshremote [-h] --path [path] --user [user] --port [port]
                          --password  --git-remote-url [git_remote_url]
</pre>
<font size=5> This command is used to initialise ssh remote bucket.</font>
 

<pre>
Example: 
cmf init sshremote --path ssh://127.0.0.1/home/user/ssh-storage --user XXXXX --port 22 --password example@123 --git-remote-url https://github.com/user/experiment-repo.git
</pre>

<font size=5> Required Arguments</font>

<pre>
  --path [path]                           Specify to url to the bucket
  --user [user]                           Specify user
  --port [port]                           Specify Port
  --password [password]                   Specify a password. This will be saved only on local
  --git-remote-url [git_remote_url]       Url to git repo
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help  show this help message and exit
  --cmf-server-ip [cmf_server_ip]   Specify cmf-server IP. (default: http://127.0.0.1:80)
</pre>

## <font size=6>**cmf artifact**</font> 

<pre>
Usage: cmf artifact [-h] {pull,push}
</pre>
<font size=5> This command pulls and push artifact to various repos.</font>
***
### 1.    cmf artifact pull
<pre>
Usage: cmf artifact pull [-h] -p [pipeline_name] -f [file_name]
</pre>
<font size=5> This command pulls artifacts from different repos to local.</font>
<pre>
Example: cmf artifact pull -p 'Test-env'  
</pre>

<font size=5> Required Arguments</font>

<pre>
  -p [pipeline_name], --pipeline-name [pipeline_name]   Specify Pipeline name

</pre>

<font size=5> Optional Arguments</font>


<pre>
  -h, --help                                  show this help message and exit
  -f [file_name],--file-name [file_name]      Specify mlmd file name
</pre>
***
### 2.    cmf artifact push
<pre>
Usage: cmf artifact push [-h] -p [pipeline_name] -f [file_name]
</pre>
<font size=5> This command pushes artifacts from local to various buckets. </font>
<pre>
Example: cmf artifact push  
</pre>

## <font size=6>**cmf metadata**</font> 


<pre>
Usage: cmf metadata [-h] {pull,push}
</pre>

<font size=5> This command pulls and push the metadata file to and from cmf-server respectively.</font>



***
###  1.   cmf metadata pull
<pre>
Usage: cmf metadata pull [-h] -p [pipeline_name] -f [file_path]  -e [exec_id]
</pre>
<font size=5> This command pulls a metadata file from cmf-server to local.</font>

<pre>
Example: cmf metadata pull -p 'Test-env' -f "/home/user/example/name_of_file"
</pre>

<font size=5> Required Arguments</font>

<pre>
  -p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name
  -f [file_path], --file_path [file_path]                 Specify a location to pull mlmd file

</pre>

<font size=5> Optional Arguments</font>

<pre>
-h, --help                                  show this help message and exit
-e [exec_id], --execution [exec_name]         Specify execution id

</pre>
***
### 2.    cmf metadata push
<pre>
Usage: cmf metadata push [-h] -p [pipeline_name] -f [file_name]  -e [exec_id]
</pre>
<font size=5> This command pushes the metadata file from local to cmf-server. </font>

<pre>
Example: cmf metadata push -p 'Test-env' -f "/home/user/example/name_of_file"
</pre>

<font size=5> Required Arguments</font>

<pre>
-p [pipeline_name], --pipeline_name [pipeline_name]     Specify Pipeline name
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help                                    show this help message and exit
  -f [file_name], --file_name [file_name]       Specify mlmd file name
  -e [exec_name], --execution [exec_name]       Specify execution id
</pre>









            



