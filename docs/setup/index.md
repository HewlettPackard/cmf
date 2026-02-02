# CMF Installation & Setup Guide


This guide provides step-by-step instructions for installing, configuring, and using CMF (Common Metadata Framework) for ML pipeline metadata tracking.

## Overview

The installation process consists of the following components:

1. **[cmflib with CMF Client Installation](#install-cmf-library-ie-cmflib)**: A Python library that captures and tracks metadata throughout your ML pipeline, including datasets, models, and metrics.
2. **[CMF Server with GUI Installation](#install-cmf-server-with-gui)**: A centralized server that aggregates metadata from multiple clients and provides a web-based graphical interface for visualizing pipeline executions, artifacts, and lineage relationships.

> **Note:** Every CMF setup requires a CMF Server instance. In collaborative environments, multiple users working on the same project can share a single CMF Server to centralize metadata and facilitate team coordination.

---

## Common Prerequisites

Before installing `cmflib` and its components, ensure you have the following:

- **Linux/Ubuntu/Debian**

- **Python**: Version 3.9 to 3.11 (3.10 recommended)

    > **Note:** If you encounter issues with Python 3.9 on Ubuntu, refer to the [Troubleshooting](#troubleshooting) section at the end of this guide.

---

## `cmflib` with CMF Client Installation {#install-cmf-library-ie-cmflib}

### Prerequisites

- **Git**: Latest version for code versioning

    > Make sure Git is properly configured using `git config`, as it's required for the product.
    > At minimum, set your user identity:
    > 
    > ```bash
    > git config --global user.name "Your Name"
    > git config --global user.email "you@example.com"
    > ```

- **Storage Backend**: local, S3, [MinIOS3](./../cmf_client/minio-server.md), [ssh storage](./../cmf_client/ssh-setup.md) or [OSDF](./../cmf_client/cmf_osdf.md) storage for artifacts.

### Installation Steps

#### Step 1: Set up Python Virtual Environment

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

#### Step 2: Install cmflib

=== "Stable version from PyPI"
    ```shell
    pip install cmflib
    ```

=== "Latest version from GitHub"
    ```shell
    pip install git+https://github.com/HewlettPackard/cmf
    ```

---

## CMF Server with GUI Installation {#install-cmf-server-with-gui}

Every CMF setup requires a CMF Server instance. In collaborative environments, multiple users working on the same project can share a single CMF Server to centralize metadata and facilitate team coordination.

### Prerequisites

- **Docker**: For containerized deployment of `CMF Server` and `CMF UI`

    > 1. Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) with [non-root user](https://docs.docker.com/engine/install/linux-postinstall/) privileges.
    > 2. Install [Docker Compose Plugin](https://docs.docker.com/compose/install/linux/).
    > 
    > In earlier versions of Docker Compose, `docker compose` was independent of Docker. Hence, `docker-compose` was the command. However, after the introduction of Docker Compose Desktop V2, the compose command became part of Docker Engine. The recommended way to install Docker Compose is by installing a Docker Compose plugin on Docker Engine. For more information - [Docker Compose Reference](https://docs.docker.com/compose/reference/).

- **Docker Proxy Settings**: Needed for some of the server packages

    > Refer to the official Docker documentation for comprehensive instructions: [Configure the Docker Client for Proxy](https://docs.docker.com/network/proxy/#configure-the-docker-client).

### Installation Steps

**Step 1: Clone the GitHub Repository**

```bash
git clone https://github.com/HewlettPackard/cmf
```

**Step 2: Navigate to the CMF Directory**

```bash
cd cmf
```

**Step 3: Create Environment Configuration**

Create a `.env` file in the same directory as `docker-compose-server.yml` with the following environment variables:

```env
CMF_DATA_DIR=./data                    
NGINX_HTTP_PORT=80                  
NGINX_HTTPS_PORT=443
REACT_APP_CMF_API_URL=http://your-server-ip:80
```

> 📝 **Note:** 
> - `CMF_DATA_DIR` controls where all data (PostgreSQL, TensorBoard logs, etc.) is stored. Use an absolute path for better control.
> - `REACT_APP_CMF_API_URL` should point to your server's accessible address.

**Step 4: Start the Containers**

> 💡 **Recommended Approach:** Using `docker compose` starts the `CMF Server`, PostgreSQL database, and `CMF UI` together.
> 
> **Note:** It's essential to start the PostgreSQL database before the `CMF Server`.

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

#### Accessing the CMF UI

Once the containers are successfully started, the CMF UI will be available at the URL specified in your `.env` file:

```
http://your-server-ip:80
```

Replace `your-server-ip` with the actual IP address or hostname configured in the `REACT_APP_CMF_API_URL` environment variable.

> 📝 **Note:** Ensure that port 80 (or your configured `NGINX_HTTP_PORT`) is accessible and not blocked by firewall rules.

**Step 5: Stop the Containers**

```bash
docker compose -f docker-compose-server.yml stop
```

#### Important Notes

> 💡 **Rebuild Required:** 
> Rebuild the images for `CMF Server` and `CMF UI` after a CMF version update or pulling the latest changes from Git to ensure compatibility.
>
> ```bash
> docker compose -f docker-compose-server.yml build --no-cache
> docker compose -f docker-compose-server.yml up
> ```

---

## Troubleshooting

### Python 3.9 Installation Issues on Ubuntu

If you are using Python 3.9 on Ubuntu systems, you may encounter installation or virtual environment issues.

**Issue**: When creating Python 3.9 virtual environments, you may encounter:

```
ModuleNotFoundError: No module named 'distutils.cmd'
```

**Root Cause**: Python 3.9 may be missing required modules like `distutils` or `venv` when installed on Ubuntu systems.

**Resolution**:

1. Add the deadsnakes PPA (provides newer Python versions):
   
   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt-get update
   ```
2. Install Python 3.9 with required modules:
   
   ```bash
   sudo apt install python3.9 python3.9-dev python3.9-distutils python3.9-venv
   ```
3. Verify the installation:
   
   ```bash
   python3.9 --version
   python3.9 -m venv test_env
   ```

This ensures Python 3.9 and its essential modules are fully installed and functional.

> 💡 **Recommendation:** If you're starting fresh, we recommend using Python 3.10 to avoid these compatibility issues.

---
