## Steps to start the minio server
***
Object storage is an abstraction layer above the file system and helps to work with data using API.
Minio is the fastest way to start working with object storage.
It is compatible with S3, easy to deploy, manage locally, and upscale if needed.

In this article, we will deploy a minio server.

1. Copy contents of the `example-get-started` directory to a separate directory outside this repository.


2. First check whether the current directory is already initialized.
<pre>cmf init show</pre>


You should see something like this on your command line.

<pre>
'cmf' is not configured.
Execute the 'cmf init' command.
</pre>

3.  Execute the following command to initialize the minioS3 repository

         cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key minioadmin --git-remote-url https://github.com/user/experiment-repo.git

Now check the cmf init status by executing the `cmf init show` command.
You will see the following output.
    
    
       remote.minio.url=s3://bucket-name
       remote.minio.endpointurl=http://localhost:9000
       remote.minio.access_key_id=minioadmin
       remote.minio.secret_access_key=minioadmin
       core.remote=minio

4. Here we are building a minio server using a Docker container. We have created docker-compose.yml which provides two services: `minio` and `aws-cli`.
   In minio, we define the release version to install and the command to run the minio server. We also define the aws-cli image to build S3 storage locally.
   We are initializing the repository with bucket name, storage URL, and credentials to access minio.
   
         docker-compose up / docker compose up
    
    After we run the above command we will see the messages that minio is up and running.
    By going on the URL `https://localhost:9000` use login and password created previously to access the UI.
    
    Given below is the example of a minio server with a dvc-art bucket.
    ![image](https://miro.medium.com/max/1100/1*sIOUllU2O6YGdT7ARoY-xw.webp)