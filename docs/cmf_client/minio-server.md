# MinIO S3 Artifact Repo Setup
## Steps to set up a MinIO server
Object storage is an abstraction layer above the file system and helps to work with data using API.
MinIO is the fastest way to start working with object storage.
It is compatible with S3, easy to deploy, manage locally, and upscale if needed.

Follow the below mentioned steps to set up a MinIO server:

1. Copy contents of the `example-get-started` directory to a separate directory outside the cmf repository.


2. Check whether cmf is initialized.
   ```
   cmf init show
   ```
   If cmf is not initialized, the following message will appear on the screen.
   ```
   'cmf' is not configured.
   Execute the 'cmf init' command.
   ```

3.  Execute the following command to initialize the MinIO S3 bucket as a CMF artifact repository.
    ```
    cmf init minioS3 --url s3://bucket-name --endpoint-url http://localhost:9000 --access-key-id minioadmin --secret-key   minioadmin --git-remote-url https://github.com/user/experiment-repo.git
    ```

4. Execute `cmf init show` to check the CMF configuration. The sample output looks as follows:
   ```
   remote.minio.url=s3://bucket-name
   remote.minio.endpointurl=http://localhost:9000
   remote.minio.access_key_id=minioadmin
   remote.minio.secret_access_key=minioadmin
   core.remote=minio
   ```

5. Build a MinIO server using a Docker container. `docker-compose.yml` available in `example-get-started` directory provides two services: `minio` and `aws-cli`.
   User will initialise the repository with bucket name, storage URL, and credentials to access MinIO.
6. Execute the following command to start the docker container. Following command requires root privileges.
   ```
   docker-compose up
   ```
   or
   ```
   docker compose up
   ```
   After executing the above command, following messages confirm that MinIO is up and running.

7. Login into `remote.minio.endpointurl` (in the above example - http://localhost:9000) using access-key and secret-key mentioned in cmf configuration.

8. Following image is an example snapshot of the MinIO server with bucket named 'dvc-art'.

![image](https://miro.medium.com/max/1100/1*sIOUllU2O6YGdT7ARoY-xw.webp)
