# cmf-server

__cmf-server__ is a key interface for the user to explore and track their ML training runs. It allows users to store the metadata file on the cmf-server. The user can retrieve the saved metadata file and can view the content of the saved metadata file using the UI provided by the cmf-server.

## API Reference
cmf-server APIs are organized around [FastAPI](https://fastapi.tiangolo.com/).
They accept and return JSON-encoded request bodies and responses and return standard HTTP response codes.

### List of APIs
   
| Method | URL                          | Description                                  | 
|--------|------------------------------|----------------------------------------------|
| `Post` | `/mlmd_push`                 | Used to push Json Encoded data to cmf-server |
| `Get`  | `/mlmd_pull/{pipeline_name}` | Retrieves a mlmd file from cmf-server        |
| `Get`  | `/display_executions`        | Retrieves all executions from cmf-server     |
| `Get`  | `/display_artifacts`         | Retrieves all artifacts from cmf-server      |

### HTTP Response Status codes

| Code  | Title                     | Description                                                  |
|-------| ------------------------- |--------------------------------------------------------------|
| `200` | `OK`                      | mlmd is successfully pushed (e.g. when using `GET`, `POST`). |
| `400` | `Bad request`             | When the cmf[env](cmf%2Fenv)-server is not available.                        |
| `500` | `Internal server error`   | When an internal error has happened                          |


## Setup a cmf-server

There were are two ways to start cmf server - 
- Using docker compose file
- Using docker run

### Pre-requisite 
1. Install [Docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non root user](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) privileges.

## Using docker compose file 
> This is the recommended way as docker compose starts both ui-server and cmf-server in one go.

1. Go to root `cmf` directory.
2. Create a directory which will be used as volume mount for docker containers.
   ```
   mkdir /home/<user>/cmf-server/data/static
   ```
   
3.  Edit `docker-compose-server.yml` with above directory.
  ```
  ......
  services:
  server:
    image: server:latest
    volumes:
      - /home/<user>/cmf-server/data:/cmf-server/data
    container_name: cmf-server
    build:
    ....
  ```
  
 4. Execute following command to start both the containers. `IP` variable is the IP address of the machine on which you are executing the following command.
    ```
    IP=200.200.200.200 docker compose -f docker-compose-server.yml up
    ```

5. Stop the containers. 
   ```
   docker compose -f docker-compose-server.yml stop
   ```

## Using docker run

1.  Install [cmflib](../index.md#installation) on your system.

2. Go to `server` directory. 
   ```
   cd server
   ```
3. List all docker images.
   ```
   docker images
   ```

4. Execute the below-mentioned command to create a `cmf-server` docker image.
   ```
   Usage:  docker build -t [image_name] -f ./Dockerfile ../
   ```
   Example:
   ```
   docker build -t myimage -f ./Dockerfile ../
   ```
   `Note` - `'../'`  represents the [Build context](https://docs.docker.com/build/building/context/) for the docker image.


5. Launch a new docker container using the image with directory /home/<user>/cmf-server/data/static mounted.
   pre-requisite - `mkdir /home/<user>/cmf-server/data/static`
   <pre>
   Usage: docker run --name [container_name] -p 0.0.0.0:8080:80 -v /home/<user>/cmf-server/data/static:/cmf-server/data/static [image_name]
   </pre>
   Example:
   ```
   docker run --name mycontainer -p 0.0.0.0:8080:80 -v /home/user/cmf-server/data/static:/cmf-server/data/static myimage
   ```

6. To stop the docker container.
   ```
   docker stop [container_name]
   ```

7. To delete the docker container.
   ```
   docker rm [container_name] 
   ```

8. To remove the docker image.
   ``` 
   docker image rm [image_name] 
   ```
