## Getting started with CMF Commands

## 1. cmf init
<pre>
Usage: cmf init [-h] {pull,push}
</pre>
<font size=5> This command is used initialize CMF for multiple repos, such as Local, minioS3, amazon s3, SSH remote.</font>
<font size=5> It is the first command to initiate CMF command line.</font>

### a.    cmf init show
<pre>
Usage: cmf init show
</pre>
<font size=5> This command is used to show cmf config.</font>


### b.    cmf init minioS3
<pre>
Usage: cmf init minioS3 [-h] --url [url] --endpoint-url [endpoint_url]
                        --access-key-id [access_key_id] --secret-key [secret_key]
</pre>
<font size=5> This command configures minioS3 server.</font>

<pre>
Example: cmf init minioS3 --url s3://dvc-art --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin
</pre>

<font size=5> Required Arguments</font>

<pre>
  --url [url]                           Specify url to bucket
  --endpoint-url [endpoint_url]         Specify endpoint url which is used to access minio locally/remotely running UI
  --access-key-id [access_key_id]       Specify Access Key Id
  --secret-key [secret_key]             Specify Secret Key

</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help  show this help message and exit
</pre>





### c.    cmf init local
<pre>
Usage: cmf init local [-h] --url [url] --git-remote-url [git_remote_url]
</pre>
<font size=5> This command is used to initialise local bucket.  This commands sets server details. </font>

<pre>
Example: cmf init local --url example needed
</pre>

<font size=5> Required Arguments</font>

<pre>
  --url [url]                           Specify url to bucket.
  --git-remote-url [git_remote_url]     Url to git repo
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help   show this help message and exit

</pre>

### d.    cmf init amazon S3
<pre>
usage: cmf init amazonS3 [-h] --url [url] --access-key-id [access_key_id]
                         --secret-key [secret_key]
</pre>
<font size=5> This command is used to initialise amazon S3 bucket. </font>
 
<font size=5> Required Arguments</font>

<pre>
  --url [url]                           Specify url to bucket
  --access-key-id [access_key_id]       Specify Access Key Id
  --secret-key [secret_key]             Specify Secret Key

</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help  show this help message and exit

</pre>

<pre>
Example: cmf init amazonS3 --url 
</pre>

### e.    cmf init SSH remote
<pre>
usage: cmf init sshremote [-h] --url [url] --user [user] --port [port]
                          --password  --git-remote-url
</pre>
<font size=5> This is command is used to initialise ssh remote bucket.</font>
 

<pre>
Example: cmf init sshremote --url 
</pre>

<font size=5> Required Arguments</font>

<pre>
  --url [url]                             Specify url to bucket
  --user [user]                           Specify user
  --port [port]                           Specify Port
  --password [password]                   Specify password. This will be saved only on local
  --git-remote-url [git_remote_url]       Url to git repo
</pre>

<font size=5> Optional Arguments</font>

<pre>
  -h, --help  show this help message and exit
</pre>

## 2. cmf artifact
<pre>
Usage: cmf artifact [-h] {pull,push}
</pre>
<font size=5> This command pulls and pushes artifacts to various repos.</font>

### a.    cmf artifact pull
<pre>
Usage: cmf artifact pull [-h] -p [pipeline_name] -f [file_name]
</pre>
<font size=5> This command pulls artifacts from different repos to local</font>
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

### b.    cmf artifact push
<pre>
Usage: cmf artifact push [-h] -p [pipeline_name] -f [file_name]
</pre>
<font size=5> This command pushes artifacts from local to various buckets </font>
<pre>
Example: cmf artifact push -p 'Test-env' 
</pre>

## 3. cmf metadata
<pre>
Usage: cmf metadata [-h] {pull,push}
</pre>
<font size=5> This command pulls and pushes metadata file from HP server.</font>




###  a.   cmf metadata pull
<pre>
Usage: cmf metadata pull [-h] -p [pipeline_name] -f [file_name]  -e [exec_name]
</pre>
<font size=5> This command pulls metadata file from server to local</font>

<font size=5> Required Arguments</font>

<pre>
  -p [pipeline_name], --pipeline_name [pipeline_name]      Specify Pipeline name
  -f [file_name], --file_name [file_name]                  Specify location to pull mlmd file

</pre>

<font size=5> Optional Arguments</font>

<pre>
-h, --help                                      show this help message and exit
-e [exec_name], --execution [exec_name]         Get execution from execution id

</pre>

### b.    cmf metadata push
<pre>
Usage: cmf metadata push [-h] -p [pipeline_name] -f [file_name]  -e [exec_name]
</pre>
<font size=5> This command pushes metadata file from local to server </font>

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
  -e [exec_name], --execution [exec_name]       Get execution from execution id
</pre>









            



