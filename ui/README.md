# Set up a UI Server

There are two ways to start a UI server -

- Using docker compose file
- Using docker run

### Prerequisites
1. Clone the [GitHub repository](https://github.com/HewlettPackard/cmf).
   ```
   git clone https://github.com/HewlettPackard/cmf
   ```

2. Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non-root user](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) privileges.
3. Install [Docker Compose Plugin](https://docs.docker.com/compose/install/linux/).
   > In earlier versions of Docker Compose, `docker compose` was independent of Docker. Hence, `docker-compose` was the command. However, after the introduction of Docker Compose Desktop V2, the compose command became part of Docker Engine. The recommended way to install Docker Compose is by installing a Docker Compose plugin on Docker Engine. For more information - [Docker Compose Reference](https://docs.docker.com/compose/reference/).
4. **Docker Proxy Settings** are needed for some of the server packages. Refer to the official Docker documentation for comprehensive instructions: [Configure the Docker Client for Proxy](https://docs.docker.com/network/proxy/#configure-the-docker-client).

## Using `docker compose` file 
> This is the recommended way as docker compose starts cmf-server, postgres db and ui-server in one go. It is neccessary to start postgres db before cmf-server.

1. Go to root `cmf` directory. 
2. Replace `xxxx` with your user-name in docker-compose-server.yml available in the root cmf directory.
    ```
    ......
    services:
    server:
      image: server:latest
      volumes:
         - /home/xxxx/cmf-server/data:/cmf-server/data                 # for example /home/hpe-user/cmf-server/data:/cmf-server/data
         - /home/xxxx/cmf-server/data/static:/cmf-server/data/static   # for example /home/hpe-user/cmf-server/data/static:/cmf-server/data/static
      container_name: cmf-server
      build:
    ....
    ``` 
3. Create a `.env` file in the same directory as `docker-compose-server.yml` and add the necessary environment variables.
   ```
   POSTGRES_USER: myuser
   POSTGRES_PASSWORD: mypassword
   POSTGRES_PORT: 5470
   ``` 
   > ⚠️**Warning:** Avoid using `@` character in `POSTGRES_PASSWORD` to prevent connection issues.
4. Execute one of the following commands to start both containers. `IP` variable is the IP address and `hostname` is the host name of the machine on which you are executing the following command.
   ```
   IP=200.200.200.200 docker compose -f docker-compose-server.yml up
              OR
   hostname=host_name docker compose -f docker-compose-server.yml up
   ```
   > Replace `docker compose` with `docker-compose` for older versions.
   > Also, you can adjust `$IP` in `docker-compose-server.yml` to reflect the server IP and run the `docker compose` command without specifying
    IP=200.200.200.200.
     ```
     .......
     environment:
     REACT_APP_MY_IP: ${IP}
     ......
     ```

5. Stop the containers.
    ```
      docker compose -f docker-compose-server.yml stop
    ```

> It is necessary to rebuild images for cmf-server and ui-server after `cmf version update` or after pulling the latest cmf code from git.

 **<h3 align="center">OR</h3>**

## Using `docker run` command

1.  Install [cmflib](./../docs/cmf_client/Getting%20Started%20with%20cmf.md) on your system.

2. Go to `cmf/server` directory.
   ```
   cd server
   ```
3. List all docker images.
   ```
   docker images
   ```

4. Execute the following command to create a `cmf-server` docker image.
   ```
   Usage:  docker build -t [image_name] -f ./Dockerfile ../
   ```
   Example:
   ```
   docker build -t server_image -f ./Dockerfile ../
   ```
   `Note` - `'../'`  represents the [Build context](https://docs.docker.com/build/building/context/) for the docker image.

5. Launch a new docker container using the image with directory /home/user/cmf-server/data mounted.
   `Pre-requisite: mkdir /home/<user>/cmf-server/data/static`
   ```
   Usage: docker run --name [container_name] -p 0.0.0.0:8080:80 -v /home/<user>/cmf-server/data:/cmf-server/data -e MYIP=XX.XX.XX.XX [image_name]
   ```
   Example:
   ```
   docker run --name cmf-server -p 0.0.0.0:8080:80 -v /home/user/cmf-server/data:/cmf-server/data -e MYIP=0.0.0.0 server_image
   ```

6. After the cmf-server container is up, start `ui-server`. Go to `cmf/ui` folder.
   ```
   cd cmf/ui
   ```

7. Execute the below-mentioned command to create a `ui-server` docker image.
   ```
   Usage:  docker build -t [image_name] -f ./Dockerfile ./
   ```
   Example:
   ```
   docker build -t ui_image -f ./Dockerfile ./
   ```

8. Launch a new docker container for UI.
   ```
   Usage: docker run --name [container_name] -p 0.0.0.0:3000:3000 -e REACT_APP_MY_IP=XX.XX.XX.XX [image_name]
   ```
   Example:
   ```
   docker run --name ui-server -p 0.0.0.0:3000:3000 -e REACT_APP_MY_IP=0.0.0.0 ui_image
   ```
      Note:
      If you face issues regarding `Libzbar-dev` similar to the snapshot, add proxies to '/.docker/config.json'

      ![Screenshot (115)](https://github.com/varkha-d-sharma/cmf/assets/111754147/9830cbe9-bad8-404a-8abe-5470fc2303c4)

      ```
      {
         proxies: {
              "default": {
                           "httpProxy": "http://web-proxy.labs.xxxx.net:8080",
                           "httpsProxy": "http://web-proxy.labs.xxxx.net:8080",
                           "noProxy": ".labs.xxxx.net,127.0.0.0/8"
                   }
               }
       }
      ```

10. To stop the docker container.
    ```
    docker stop [container_name]
    ```

11. To delete the docker container.
    ```
    docker rm [container_name]
    ```

12. To remove the docker image.
    ```
    docker image rm [image_name]
    ```
