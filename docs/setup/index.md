# `cmf` Installation & Setup Guide

This guide provides step-by-step instructions for installing, configuring, and using CMF (Common Metadata Framework) for ML pipeline metadata tracking.

The installation process consists of following components:

1. **cmflib**: exposes APIs to track the pipeline metadata. It also provides APIs to query the stored metadata.
2. **cmf-server with GUI**: enables users to store, retrieve, and view ML training metadata through an intuitive UI.
---

## Prerequisites

Before installing CMF, ensure you have the following prerequisites:

- **Linux/Ubuntu/Debian**
- **Python**: Version 3.9 to 3.11 (3.10 recommended)
  
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
  >     
  >    ```bash
  >    sudo add-apt-repository ppa:deadsnakes/ppa
  >    sudo apt-get update
  >   ```
  >    
  > 2. Install Python 3.9 with required modules:
  >    
  >   ```bash
  >   sudo apt install python3.9 python3.9-dev python3.9-distutils
  >   ```
  >   
  >   This ensures Python 3.9 and its essential modules are fully installed.

- **Git**: Latest version for code versioning.
  > Make sure Git is properly configured using `git config`, as it's required for the product.
  > At minimum, set your user identity:
  > ```bash
  >  git config --global user.name "Your Name"
  >  git config --global user.email "you@example.com"
  >  ```

- **Docker** : For containerized deployment of `cmf-server` and `cmf-gui`.
  > 1. Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non-root user](https://docs.docker.com/engine/install/linux-postinstall/) privileges.
  > 2. Install [Docker Compose Plugin](https://docs.docker.com/compose/install/linux/).
  > In earlier versions of Docker Compose, `docker compose` was independent of Docker. Hence, `docker-compose` was the command. However, after the introduction of Docker Compose Desktop V2, the compose command became part of Docker Engine. The recommended way to install Docker Compose is by installing a Docker Compose plugin on Docker Engine. For more information - [Docker Compose Reference](https://docs.docker.com/compose/reference/).
- **Docker Proxy Settings** are needed for some of the server packages. Refer to the official Docker documentation for comprehensive instructions: [Configure the Docker Client for Proxy](https://docs.docker.com/network/proxy/#configure-the-docker-client).
- **Storage Backend**: S3, [MinIOS3](./../cmf_client/minio-server.md), [ssh storage](./../cmf_client/ssh-setup.md), [OSDF](./../cmf_client/cmf_osdf.md) or local storage for artifacts.
---

## Components

### Install cmf library i.e. cmflib
---

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

**2. Install CMF:**

=== "Latest version from GitHub"
    ```shell
    pip install git+https://github.com/HewlettPackard/cmf
    ```

=== "Stable version from PyPI"
    ```shell
    # pip install cmflib
    ```

### Install cmf-server with GUI
---

- Ensure that Docker is installed on your machine, as mentioned in the [prerequisites](#prerequisites). If not, please install it before proceeding.

- Clone the [GitHub repository](https://github.com/HewlettPackard/cmf).
     ```
     git clone https://github.com/HewlettPackard/cmf
     ```

- Using `docker compose` File

> This is the recommended approach, as `docker compose` starts the `cmf-server`, PostgreSQL database, and `cmf-gui` together.
> **Note:** It's essential to start the PostgreSQL database before the `cmf-server`.
1. **Navigate to the `cmf` directory:**

   ```bash
   cd cmf
   ```

2. **Create a `.env` file in the same directory as `docker-compose-server.yml` with environment variables:**

   **Required variables:**
   ```env
   CMF_DATA_DIR=./data                    
   NGINX_HTTP_PORT=80                  
   NGINX_HTTPS_PORT=443
   REACT_APP_CMF_API_URL=http://your-server-ip:80
   ```
   
   > 📝 **Note:** 
   > - `CMF_DATA_DIR` controls where all data (PostgreSQL, TensorBoard logs, etc.) is stored. Use an absolute path for better control.
   > - `REACT_APP_CMF_API_URL` should point to your server's accessible address.

3. **Start the containers:**

   ```bash
   docker compose -f docker-compose-server.yml up
   ```

   > 📝 **Note:** Replace `docker compose` with `docker-compose` if you're using an older version of Docker.

   This command starts all services:
   - **PostgreSQL**: Database backend for metadata storage
   - **CMF Server**: API server for metadata management
   - **UI**: Web interface for visualization
   - **TensorBoard**: For viewing ML training metrics
   - **Nginx**: Reverse proxy serving all components

4. **Stop the containers:**   ```bash
   docker compose -f docker-compose-server.yml stop
   ```

---

> 💡 **Important:**
> Rebuild the images for `cmf-server` and `cmf-ui` after a `cmf` version update or pulling the latest changes from Git to ensure compatibility.

---
