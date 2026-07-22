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
