# cmf-server
***
## Overview

 <font size=5>__cmf-server__</font> <font size=5> is a key interface for the user to explore and track their ML training runs. It allows users to store and retrieve metadata files on and from the server, respectively, with the help of different APIs.
 It enables a UI to track various stages, executions, and artifacts.
***
## Table of contents
- API Reference
- Steps to activate cmf-server
***
## 1. API Reference
<font size=5>cmf-server APIs are organized around [FastAPI](https://fastapi.tiangolo.com/).
They accept and return JSON-encoded request bodies and responses and return standard HTTP response codes.</font>
1. <font size=5>**List of APIs**</font>

    
| Method | URL                          | Description                                  | 
|--------|------------------------------|----------------------------------------------|
| `Post` | `/mlmd_push`                 | Used to push Json Encoded data to cmf-server |
| `Get`  | `/mlmd_pull/{pipeline_name}` | Retrieves a mlmd file from cmf-server        |
| `Get`  | `/display_executions`        | Retrieves all executions from cmf-server     |
| `Get`  | `/display_artifacts`         | Retrieves all artifacts from cmf-server      |

2. <font size=5>**HTTP Response Status codes**</font>


| Code  | Title                     | Description                                                  |
|-------| ------------------------- |--------------------------------------------------------------|
| `200` | `OK`                      | mlmd is successfully pushed (e.g. when using `GET`, `POST`). |
| `400` | `Bad request`             | When the cmf-server is not available.                        |
| `500` | `Internal server error`   | When an internal error has happened                          |

***
## 2. Steps to activate cmf-server

   <font size=5>cmf-server has been containerized with docker. Pre-requisite [Docker]()
1. Install [cmflib](https://github.com/abhinavchobey/cmf/blob/federated_cmf/README.md) on your system.


2. Go to 'server' directory. 
```
      user@uservm:~/cmf$ cd server
```

3. To execute docker commands, the user needs root privileges. 
```
      sudo su
```
4. List all docker images.
```
      docker images
```

5. Execute the below-mentioned command to create the 'cmf-server' docker image.
```
      docker build -t [image_name] -f ./Dockerfile ../
```

Note - `'../'`  represents the [Build context](https://docs.docker.com/build/building/context/) for the docker image.

6. Launch a docker container using the image created in the previous step. We will name the container and run it with the command 
```
      docker run --name [container_name] --port 80:80 [image_name]
```

7. To stop the docker container.
```
      docker stop [container_name]
```

8. To delete the docker container.
```
      docker rm [container_name] 
```

9. To remove the docker image.
```
      docker image rm [image_name] 
```