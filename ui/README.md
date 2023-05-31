# Set up a UI Server

There were are two ways to start UI server - 
- Using docker compose file
- Using docker run

## Pre-Requisites
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
> Following steps will start UI server only. It is recommended to start `cmf-server` before starting UI server. Follow [here](../docs/cmf_server/cmf-server.md) for details on how to setup a cmf-server.
1.  Install [cmflib](../index.md#installation) on your system.

2. Go to `ui` directory. 
   ```
   cd ui
   ```
3. List all docker images.
   ```
   docker images
   ```

4. Execute the below-mentioned command to create a `cmf-server` docker image.
   ```
   Usage:  docker build -t [image_name] -f ./Dockerfile . 
   ```
   Example:
   ```
   docker build -t ui-image -f ./Dockerfile .
   ```
   `Note` - `'.'`  represents the [Build context](https://docs.docker.com/build/building/context/) for the docker image.


5. Launch a new docker container using the image.
   <pre>
   Usage: docker run --name [container_name] -p 0.0.0.0:3000:3000 [image_name]
   </pre>
   Example:
   ```
   docker run --name ui-container -p 0.0.0.0:3000:3000 ui-image
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
