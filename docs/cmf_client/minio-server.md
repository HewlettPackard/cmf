# MinIO S3 Artifact Repository Setup
## Steps to set up a MinIO server
Object storage is an abstraction layer above the file system that provides an API to
interact with data. MinIO is an easy way to start working with object storage. It
is compatible with S3, easy to deploy, manage locally, and scale if needed.

Follow the steps below to set up a MinIO server:

1. Copy the contents of the `example-get-started` directory to a separate directory outside the cmf repository.

2. Check whether cmf is initialized.
   ```
   cmf init show
   ```
   If cmf is not initialized, the following message will appear on the screen:
   ```
   'cmf' is not configured.
   Execute the 'cmf init' command.
   ```

3. Execute the following command to initialize the MinIO S3 bucket as a CMF artifact repository:
    ```
    cmf init minioS3 --url s3://dvc-art --endpoint-url http://x.x.x.x:9000 \
      --access-key-id minioadmin --secret-key minioadmin \
      --git-remote-url https://github.com/user/experiment-repo.git \
      --cmf-server-url http://x.x.x.x:80  --neo4j-user neo4j \
      --neo4j-password password --neo4j-uri bolt://localhost:7687
    ```

   > Here, "dvc-art" is provided as an example bucket name. However, users can change it as needed. If the user chooses to change it, they will need to update the Dockerfile for minioS3 accordingly.

4. Execute `cmf init show` to check the CMF configuration. The sample output looks as follows:
   ```
   remote.minio.url=s3://bucket-name
   remote.minio.endpointurl=http://localhost:9000
   remote.minio.access_key_id=minioadmin
   remote.minio.secret_access_key=minioadmin
   core.remote=minio
   ```

5. Build a MinIO server using a Docker container. The `docker-compose.yml` available in the
   `example-get-started` directory provides two services: `minio` and `aws-cli`. The user
   will initialize the repository with the bucket name, storage URL, and credentials to
   access MinIO.

6. Execute the following command to start the Docker container. The MYIP variable is the IP address of the machine on which you are executing the following command. The following command requires root privileges.
   ```
   MYIP=XX.XX.XXX.XXX docker-compose up
   ```
   or
   ```
   MYIP=XX.XX.XXX.XXX docker compose up
   ```
   You should see output confirming that MinIO is up and running.
   > Also, you can adjust `$MYIP` in `examples/example-get-started/docker-compose.yml` to specify
    the server IP and run the `docker compose` command without specifying MYIP above.

7. Login into `remote.minio.endpointurl` (in the above example - http://localhost:9000) using
   the access-key and the secret-key defined in the `cmf init` command.

8. The following image is a snapshot of this example using a MinIO server and a bucket named 'dvc-art'.

![image](https://miro.medium.com/max/1100/1*sIOUllU2O6YGdT7ARoY-xw.webp)

