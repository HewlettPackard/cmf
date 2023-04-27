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

### Pre-requisite 
1. Install [Docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non root user](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) privileges.

 ### Following steps start a cmf-server in a docker conatainer:
1.  Install [cmflib](../index.md#installation) on your system.

2. Go to **server** directory. 
```
cd server
```

3. List all docker images.
```
docker images
```

4. Execute the below-mentioned command to create a **cmf-server** docker image.
<pre>
Usage:  docker build -t [image_name] -f ./Dockerfile ../
</pre>
Example:
```
docker build -t myimage -f ./Dockerfile ../
```
Note - `'../'`  represents the [Build context](https://docs.docker.com/build/building/context/) for the docker image.

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
