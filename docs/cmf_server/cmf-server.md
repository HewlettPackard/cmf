# cmf-server
***
## Overview

 <font size=5>__cmf-server__</font> <font size=5> is a key interface for the user to explore and track their ML training runs. It allows users to store and retrieve
Metadata files on the server with the help of different APIs, Also it enables a UI to track various stages, executions, and artifacts. </font>
***
## Table of contents
- API Reference
- Steps to activate cmf-server
***
## 1. API Reference
<font size=5>The cmf-server API is organized around FASTapi. Our APIs accept and returns JSON-encoded 
request bodies and responses. It uses standard HTTP response codes.</font>

1. <font size=5>**API's Available**</font>

    <font size=5>The request method is the way we distinguish what kind of action our endpoint is being asked to perform. We have a few methods that we use quite often.</font>

| Method | URL                          | Description                                  | 
|--------|------------------------------|----------------------------------------------|
| `Post` | `/mlmd_push`                 | Used to push Json Encoded data to cmf-server |
| `Get`  | `/mlmd_pull/{pipeline_name}` | Retrieves a mlmd file from cmf-server        |
| `Get`  | `/display_executions`        | Retrieves all executions from cmf-server     |
| `Get`  | `/display_artifacts`         | Retrieves all artifacts from cmf-server      |

2. <font size=5>**HTTP Response Status codes**</font>

One of the most important things in an API is how it returns response codes. Each response code means a different thing and consumers of  API rely heavily on these codes.

| Code  | Title                     | Description                                                  |
|-------| ------------------------- |--------------------------------------------------------------|
| `200` | `OK`                      | mlmd is successfully pushed (e.g. when using `GET`, `POST`). |
| `400` | `Bad request`             | When the cmf-server is not available.                        |
| `500` | `Internal server error`   | When an internal error has happened                          |

***
## 2. Steps to activate cmf-server

   <font size=5>cmf-server has been systemized with docker. So let's consider you have Docker installed.

1. Install cmflib on your system.

   <font size=4>For installation of cmflib click on</font> [cmflib Installation](https://github.com/abhinavchobey/cmf/blob/federated_cmf/README.md)

2.  To list all the docker images you can use the following command.
```
      docker images
```

3. To create a cmf-server docker image, redirect to the server directory under the cmf folder.


4. Build cmf-server docker image by running the following command.
```
      docker build -t [image_name] -f ./Dockerfile ../
```

      Note: You may receive an error saying Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker…

      This means the user does not have permission to access the Docker engine. Solve this problem by adding sudo before the command or run it as root.

5. Launch a new docker container based on the image you created in previous steps. We will name the container and run it with the command 
<pre>
      docker run --name [container_name] -p 80:80 [image_name]
</pre>

6. To stop the docker container.
```
      docker stop [container_name]
```

7. To stop the docker container.
<pre>
      docker rm [container_name] 
</pre>

8. To remove the docker image.
<pre>
      docker image rm [image_name] 
</pre>