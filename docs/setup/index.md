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

## CMF Server Deployment on Kubernetes {#deploy-cmf-server-on-kubernetes}

For cluster-based deployments, the CMF Server stack can be deployed on Kubernetes using the Helm chart located at `charts/cmf` in the repository. The chart deploys the same components as the Docker Compose recipe above:

- **PostgreSQL**: Database backend for metadata storage
- **CMF Server**: API server for metadata management
- **UI**: Web interface for visualization
- **TensorBoard**: For viewing ML training metrics
- **MCP Server**: MCP server for AI agent integration
- **Nginx**: Reverse proxy serving all components

### Prerequisites

- A Kubernetes cluster (v1.24 or later), with `kubectl` configured to access it
- **Helm**: Version 3.8 or later. See the [Helm installation guide](https://helm.sh/docs/intro/install/).
- **Dynamic storage provisioning**: A default `StorageClass` capable of dynamic provisioning (standard on Minikube, cloud providers, and most clusters). The chart creates `PersistentVolumeClaims` for PostgreSQL data, server data, and TensorBoard logs.

> 📝 **Note:** For Minikube, start the cluster with sufficient resources:
>
> ```bash
> minikube start --driver=docker --cpus=4 --memory=8192
> ```

### Installation Steps

**Step 1: Clone the GitHub Repository**

```bash
git clone https://github.com/HewlettPackard/cmf
cd cmf
```

**Step 2: Create a Namespace for CMF (Optional)**

```bash
kubectl create namespace cmf
```

**Step 3: Install the CMF Server Stack with Helm**

```bash
helm install cmf charts/cmf --namespace cmf
```

> 📝 **Note:** If you skipped Step 2, add `--create-namespace` to have Helm create the namespace automatically:
>
> ```bash
> helm install cmf charts/cmf --namespace cmf --create-namespace
> ```

**Step 4: Watch the Deployment**

```bash
kubectl -n cmf get pods
```

All pods should reach the `Running` status with `1/1` ready. PostgreSQL starts first; the CMF Server waits for it to be ready before starting, and the UI and MCP servers wait for the CMF Server.

**Step 5: Access the CMF UI**

The Nginx reverse proxy is exposed as a `NodePort` service:

```bash
kubectl -n cmf get svc nginx
```

Open the UI at `http://<node-ip>:30080`, where `<node-ip>` is the IP of any cluster node:

```bash
# For Minikube:
minikube ip

# Or use port-forwarding if NodePort access is not available:
kubectl -n cmf port-forward svc/nginx 8080:80
# then open http://localhost:8080
```

#### Verifying the Deployment

Confirm that all components are working:

```bash
# All pods should be Running and Ready (1/1)
kubectl -n cmf get pods

# All services should be present (nginx, server, ui, tensorboard, mcp, postgres)
kubectl -n cmf get svc -n cmf

# UI is reachable through nginx (expect HTTP 200)
curl -s -o /dev/null -w "%{http_code}\n" http://<node-ip>:30080/

# CMF Server API responds through the /api route (expect HTTP 200)
curl -s -o /dev/null -w "%{http_code}\n" http://<node-ip>:30080/api/v1/artifacts

# TensorBoard is proxied (expect HTTP 200)
curl -s -o /dev/null -w "%{http_code}\n" http://<node-ip>:30080/tensor_board/

# MCP Server health endpoint (expect HTTP 200)
curl -s -o /dev/null -w "%{http_code}\n" http://<node-ip>:30832/health

# Check logs of individual components
kubectl -n cmf logs deploy/server
kubectl -n cmf logs deploy/nginx
```

#### Connecting the CMF Client

Initialize the CMF client against the Kubernetes deployment:

```bash
cmf init local --path <local-storage-path> --git-remote-url <git-url> \
    --cmf-server-url http://<node-ip>:30080
```

### Customizing the Deployment

Configuration is done through `values.yaml`. Key options:

| Option | Default | Description |
|--------|---------|-------------|
| `nginx.service.type` | `NodePort` | Change to `LoadBalancer` or `ClusterIP` for other exposure models |
| `nginx.service.httpNodePort` | `30080` | NodePort for HTTP access to the UI/API |
| `mcp.external.nodePort` | `30832` | NodePort for external MCP access |
| `postgres.auth.user` / `postgres.auth.password` | `myuser` / `mypassword` | PostgreSQL credentials |
| `storage.mode` | `pvc` | Set to `hostPath` for Minikube-style host directories |
| `storage.<component>.size` / `storageClass` | varies | Per-component PVC sizing and storage class |
| `neo4j.enabled` | `false` | Optionally deploy Neo4j |
| `<component>.image.repository` / `tag` | `federcmf/*` | Override image registry or tags |

Apply overrides with a values file or `--set` flags:

```bash
helm upgrade cmf charts/cmf --namespace cmf -f my-values.yaml
# or, for example:
helm upgrade cmf charts/cmf --namespace cmf --set postgres.auth.password=secret
```

### Uninstallation

```bash
# Remove the CMF release (retains persistent data)
helm uninstall cmf --namespace cmf
```

To also remove the persistent data (all metadata, uploaded artifacts, and TensorBoard logs):

```bash
kubectl -n cmf delete pvc --all
```

To remove everything, including the namespace:

```bash
helm uninstall cmf --namespace cmf
kubectl delete namespace cmf
```

> ⚠️ **Warning:** Deleting PVCs permanently removes all CMF metadata and logs. Export any data you need before uninstalling.

---

## Troubleshooting

### One-Time PostgreSQL 13 to 17 Upgrade for Existing Users

After pulling the latest CMF changes, `docker-compose-server.yml` starts PostgreSQL 17 by default and stores new data in `${CMF_DATA_DIR}/postgres17_data`. Existing users may still have old PostgreSQL 13 data in `${CMF_DATA_DIR}/postgres_data`.

PostgreSQL 17 cannot directly start with a PostgreSQL 13 data directory.
> Do not copy or mount the old PostgreSQL 13 `postgres_data` directory into a PostgreSQL 17 container.

If old PostgreSQL 13 data exists, back it up with a temporary `postgres:13` container, then start the latest CMF stack so PostgreSQL 17 creates `${CMF_DATA_DIR}/postgres17_data`, and restore the backup into PostgreSQL 17. The previous version of `docker-compose-server.yml` that used PostgreSQL 13 is not required for this migration.

The migration commands use the same `.env` file as `docker compose -f docker-compose-server.yml up`. The following variables are used during the migration:

* `CMF_DATA_DIR`: locates the existing `postgres_data` directory and the new `postgres17_data` directory.
* `POSTGRES_USER`: specifies the PostgreSQL user used for readiness checks, backup, and restore.
* `POSTGRES_PASSWORD`: provides the password when starting the temporary PostgreSQL 13 container.
* `POSTGRES_DB`: specifies the CMF database to back up and restore.

If these variables are not defined in `.env`, the migration commands use the default values specified in the commands below.

**Step 1: Prepare and check the PostgreSQL data directory**

Run the following commands from the CMF repository directory. The first command loads and exports the values from `.env` into the shell so that the migration commands use the same configuration as Docker Compose.

```bash
set -a; [ -f .env ] && . ./.env; set +a

DATA_DIR="$(realpath "${CMF_DATA_DIR:-./data}")"

cat "${DATA_DIR}/postgres_data/PG_VERSION"
```

If the output is `13`, continue with the backup and restore process.

If the file does not exist, or the output is not `13`, this PostgreSQL 13 migration process is not required for that data directory.

**Step 2: Stop the current CMF stack**

Stop any running CMF services before creating the backup:

```bash
docker compose -f docker-compose-server.yml stop
```

**Step 3: Start a temporary PostgreSQL 13 container for backup**

The latest `docker-compose-server.yml` uses PostgreSQL 17, so use a temporary PostgreSQL 13 container to read the old `postgres_data` directory and create the backup:

```bash
docker run -d --name cmf-postgres13-backup \
    -e POSTGRES_USER="${POSTGRES_USER:-myuser}" \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-mypassword}" \
    -e POSTGRES_DB="${POSTGRES_DB:-mlmd}" \
    -v "${DATA_DIR}/postgres_data:/var/lib/postgresql/data" \
    docker.io/library/postgres:13
```

Wait until the temporary PostgreSQL 13 container is ready:

```bash
docker exec cmf-postgres13-backup pg_isready -U "${POSTGRES_USER:-myuser}"
```

**Step 4: Create a logical backup from PostgreSQL 13**

Back up the CMF database only. Do not use `pg_dumpall` for this restore path because the latest PostgreSQL 17 container already creates `${POSTGRES_USER}` and `${POSTGRES_DB}` during startup.

```bash
docker exec cmf-postgres13-backup pg_dump -Fc -U "${POSTGRES_USER:-myuser}" -d "${POSTGRES_DB:-mlmd}" > postgres13-mlmd.dump
```

Confirm the backup file was created:

```bash
ls -lh postgres13-mlmd.dump

test -s postgres13-mlmd.dump && echo "backup file created"
```

Remove the temporary PostgreSQL 13 container after the backup is complete:

```bash
docker rm -f cmf-postgres13-backup
```

Keep the old PostgreSQL 13 data directory until the PostgreSQL 17 restore has been verified:

```text
${DATA_DIR}/postgres_data
```

**Step 5: Confirm the latest compose file uses PostgreSQL 17**

The PostgreSQL service in `docker-compose-server.yml` should use PostgreSQL 17 and `postgres17_data`:

```yaml
postgres:
  image: docker.io/library/postgres:17
  volumes:
    - ${CMF_DATA_DIR:-./data}/postgres17_data:/var/lib/postgresql/data
```

**Step 6: Verify or start PostgreSQL 17**

First, verify whether the PostgreSQL 17 service is already running:

```bash
docker compose -f docker-compose-server.yml ps postgres
```

If the `postgres` service is listed as running or healthy, no start command is required. Continue to the version verification step below.

If the `postgres` service is not running, start only the PostgreSQL service with Docker Compose:

```bash
docker compose -f docker-compose-server.yml up -d postgres
```

Verify that PostgreSQL 17 is running:

```bash
docker compose -f docker-compose-server.yml exec -T postgres postgres --version
```

The output should start with:

```text
PostgreSQL 17
```

If postgres17_data does not already exist, starting PostgreSQL 17 creates the PostgreSQL 17 data directory at:

```text
${DATA_DIR}/postgres17_data
```

**Step 7: Restore the PostgreSQL 13 backup into PostgreSQL 17**

```bash
cat postgres13-mlmd.dump | docker compose -f docker-compose-server.yml exec -T postgres \
    pg_restore --clean --if-exists --no-owner \
    -U "${POSTGRES_USER:-myuser}" \
    -d "${POSTGRES_DB:-mlmd}"
```

**Step 8: Validate the restored PostgreSQL 17 database**

Check the database server version:

```bash
docker compose -f docker-compose-server.yml exec -T postgres \
    psql -U "${POSTGRES_USER:-myuser}" \
    -d "${POSTGRES_DB:-mlmd}" \
    -tAc "SHOW server_version;"
```

The output should start with `17`.

Check the PostgreSQL data directory version:

```bash
docker compose -f docker-compose-server.yml exec -T postgres \
    cat /var/lib/postgresql/data/PG_VERSION
```

Expected output:

```text
17
```

**Step 9: Start CMF services**

```bash
docker compose -f docker-compose-server.yml up
```

After confirming the application works with PostgreSQL 17, keep the old PostgreSQL 13 data directory for rollback until the migration is accepted.

---

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
