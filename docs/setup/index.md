# CMF Installation & Setup Guide

This guide provides step-by-step instructions for installing, configuring, and using CMF (Common Metadata Framework) for ML pipeline metadata tracking.


# CMF Installation

This hub connects you to the deployment procedures for the Common Metadata Framework (CMF). CMF separates metadata collection from visualization, requiring two distinct installation tracks depending on your user role.

## Component Overview

* **[cmflib with CMF Client Installation](./server_side_installation.md)**: A Python library that captures and tracks metadata throughout your ML pipeline, including datasets, models, and metrics.
* **[CMF Server with GUI Installation](./client_side_installation.md)**: A centralized server that aggregates metadata from multiple clients and provides a web-based graphical interface for visualizing pipeline executions, artifacts, and lineage relationships.

> **Note:** Every CMF setup requires a CMF Server instance. In collaborative environments, multiple users working on the same project can share a single CMF Server to centralize metadata and facilitate team coordination.


---

## Common Prerequisites

Ensure your target deployment nodes meet these foundational system constraints before selecting an installation track:

* **Operating System**: Linux (Ubuntu/Debian distributions strictly validated).
* **Python Engine**: Runtime versions 3.9 to 3.11 are supported (* **Recommended Runtime**: Python 3.10).<br />
> **Note:** If you encounter issues with Python 3.9 on Ubuntu, refer to the Troubleshooting section at the end of this guide..

---

# CLI Execution Reference
Before initiating the environment setup, review the foundational commands required to deploy the client.

!!! warning "Important Note"
    * The following initial steps are basic and mandatory prerequisites for both server-side and client-side installations. You must execute these core commands sequentially to prepare your environment.
<br />

**Note:** First, at the root directory, execute the ls command to check the existing workspace folder structure.<br />

**Step 1: List Directory Contents**<br/><br/>
**Description:** ls command to check the existing workspace folder structure<br/>
```bash
 $ ls
```
**Output:** Demo,  cmf_env,  cmf_workspace 
<br>

---

**Step 2: Check Installed Python Version**<br/><br/>
**Description**: Next, check the Python version at the root directory to confirm the environment meets CMF runtime constraints.<br/>

```bash
$ python --version
```
**Output:** Python 3.10.20 <br/>
If you have python version greater then 3.10 use below commands:
    <br>
    ```bash
    sudo apt update
    sudo apt install -y python3.10 python3.10-venv python3-pip
    ```

- **Python:** Version 3.9 to 3.11 (3.10 recommended)

    > **Note:** If you encounter issues with Python 3.9 on Ubuntu, refer to the [Troubleshooting](#troubleshooting) section at the end of this guide.

---

**Step 3: Create the Workspace Directory And Navigate into the Workspace Directory**<br/><br/>
**Description:** Creates a new folder named cmf_workspace to store all project assets and : Moves your terminal session into the newly created folder to execute subsequent commands.<br/>

```bash
$  mkdir cmf_workspace
cd cmf_workspace
```
**Output:** ~/cmf_workspace$

---

**Step 4: Create a Virtual Environment**<br/><br/>
**Description:** Create an isolated, self-contained Python virtual environment named cmf_env dedicated exclusively to CMF dependencies to prevent dependency pollution.<br/>

=== "Virtual Environment"
    ```shell
    python3.10 -m venv cmf_env
    ```

=== "Conda Environment"
    ```WSL
    conda create -n cmf_env python=3.10 -y
    ```

**Output:** The command will run silently and output absolutely nothing to the terminal. It simply creates the cmf_env folder.

---

**Step 5: Activate the Virtual Environment**<br/><br/>
**Description:** Activate the virtual environment to configure your path variables so all subsequent python and pip binaries resolve strictly inside this sandbox.<br/>

=== "Virtual Environment"
    ```shell
    $  source cmf_env/bin/activate
    ```

=== "Conda Environment"
    ```WSL
    conda activate cmf_env
    ```

**Output:** (cmf_env)$
<br>
Activate the virtual environment

---

**Step 6: Install the CMF Library**<br/><br/>
**Description:** Install the core cmflib client package to expose the framework APIs required to track ML workflows and push metadata streams.<br/>

=== "Virtual Environment"
    ```shell
    $  pip install cmflib
    ```

=== "Latest version from GitHub"
    ``` WSL
    pip install git+https://github.com/HewlettPackard/cmf
    ```

**Output:**
    new release of pip is available: 23.0.1<br />
    Processing /home/sanadiay/docs/cmf
    Installing build dependencies ... done
    Getting requirements to build wheel ... done
    Preparing metadata (pyproject.toml) ... done<br />
    Successfully built cmflib
    Installing collected packages: cmflib
    Attempting uninstall: cmflib
    Found existing installation: cmflib 0.0.99
    Uninstalling cmflib-0.0.99:<br />
    Successfully uninstalled cmflib-0.0.99
    Successfully installed cmflib-0.1.0
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
