# `cmf` Installation & Setup Guide

## **Overview**

This guide provides step-by-step instructions for installing, configuring, and using CMF (Common Metadata Framework) for ML pipeline metadata tracking.

The installation process consists of following components:

1. **cmflib**: exposes APIs to track the pipeline metadata. It also provides APIs to query the stored metadata.
2. **cmf-server with GUI**: enables users to store, retrieve, and view ML training metadata through an intuitive UI.
---

## **Prerequisites**

Before installing CMF, ensure you have the following prerequisites:

- **Linux/Ubuntu/Debian**
- **Python**: Version 3.9 to 3.10 (3.10 recommended)
  
  > ⚠️ **Warning:** "Python 3.9 Installation Issue on Ubuntu"
  >
  > **Issue**: When creating Python 3.9 virtual environments, you may encounter:
  > 
  > ```
  > ModuleNotFoundError: No module named 'distutils.cmd'
  > ```
  > 
  >  **Root Cause**: Python 3.9 may be missing required modules like `distutils` or `venv` when installed on Ubuntu systems.
  > 
  >  **Resolution**:
  > 
  >  1. Add the deadsnakes PPA (provides newer Python versions):
  >    ```bash
  >    sudo add-apt-repository ppa:deadsnakes/ppa
  >    sudo apt-get update
  >   ```
  > 2. Install Python 3.9 with required modules:
  >   ```bash
  >   sudo apt install python3.9 python3.9-dev python3.9-distutils
  >   ```
  >   
  >   This ensures Python 3.9 and its essential modules are fully installed.

- **Git**: Latest version for code versioning
- **Docker**: For containerized deployment
- **Storage Backend**: S3, MinIO, or local storage for artifacts
---

## **Components**

### **Install cmf library i.e. cmflib**

**1. Set up Python Virtual Environment**

=== "Using Conda"
    ```shell
    conda create -n cmf python=3.10
    conda activate cmf
    ```

=== "Using VirtualEnv"
    ```shell
    virtualenv --python=3.10 .cmf
    source .cmf/bin/activate
    ```

#### 2. Install CMF:

=== "Latest version from GitHub"
    ```shell
    pip install git+https://github.com/HewlettPackard/cmf
    ```

=== "Stable version from PyPI"
    ```shell
    # pip install cmflib
    ```

### **Install cmf-server**

**Docker Installation**

  1. Clone the [GitHub repository](https://github.com/HewlettPackard/cmf).
   ```
   git clone https://github.com/HewlettPackard/cmf
   ```

  2. Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non-root user](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) privileges.
  3. Install [Docker Compose Plugin](https://docs.docker.com/compose/install/linux/).
   > In earlier versions of Docker Compose, `docker compose` was independent of Docker. Hence, `docker-compose` was the command. However, after the introduction of Docker Compose Desktop V2, the compose command became part of Docker Engine. The recommended way to install Docker Compose is by installing a Docker Compose plugin on Docker Engine. For more information - [Docker Compose Reference](https://docs.docker.com/compose/reference/).
  4. **Docker Proxy Settings** are needed for some of the server packages. Refer to the official Docker documentation for comprehensive instructions: [Configure the Docker Client for Proxy](https://docs.docker.com/network/proxy/#configure-the-docker-client).

**Using `docker compose` file**
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

---




