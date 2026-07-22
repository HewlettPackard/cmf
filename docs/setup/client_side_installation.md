# CMF Client Installation Guide

This page covers the step-by-step setup of `cmflib` on client nodes to track and log machine learning pipeline metadata.

## Prerequisites

### 1. Git Identity Configuration
CMF relies on Git for local code lineage and version state tracking. You must configure your local Git identity:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 2. Storage Backend Architecture
Ensure you have access credentials and network pathways ready for your chosen artifact repository:
- **Storage Backend**: [local](./../cmf_client/local-storage-setup.md), S3, [MinIOS3](./../cmf_client/minio-server.md), [ssh storage](./../cmf_client/ssh-setup.md) or [OSDF](./../cmf_client/cmf_osdf.md) storage for artifacts.

---

# CLI Execution Reference
Before initiating the environment setup, review the foundational commands required to deploy the client.
Please follow the mandatory installation and setup guide before proceeding. [Installation and Setup](../../setup/#cli-execution-reference).

## Installation Steps

**Open new terminal and start the execution of commands:**<br/><br/>
**Step 1: Activate the Virtual Environment**<br/><br/>
**Description:** Activates an isolated Python environment to keep project packages separated from global system files.

=== "Virtual Environment"
    ```shell
    $ source cmf_env/bin/activate
    ```

=== "Conda Environment"
    ```shell
    conda activate cmf_env
    ```

**Output:** (cmf_env)$
<br>
Prefixes your terminal shell prompt with (cmf_env) to signal that isolation is active.

---   
**Step 2: Verify the CMF Package Installation**<br/><br/>
**Description:** Queries the Python package manager to extract technical information regarding the installed cmflib library.<br />
you have python version 3.10 and gitHub 1.9.1

```bash
$ pip show cmflib
```
**Output:** <br />
Name: cmflib,<br />
Version: 0.1.0,<br />
Summary: Track metadata for AI pipeline.<br />

Prints package metadata including the explicit name, installed version (0.1.0), and its functional summary.

---
**Step 3: Locate the CMF Executable Path**<br/><br/>
**Description:** Searches your system's environmental path variable to find the exact file location of the cmf command tool.

```bash
$  which cmf
```
**Output:**/home/user_name/cmf_env/bin/cmf
<br>

Returns the absolute directory path pointing directly to the binary executable inside your active environment.

---
**Step 4: Navigate to the CMF Workspace**<br/><br/>
**Description:** Changes your terminal's current working directory context to the specific folder named cmf_workspace.

```bash
$  cd cmf_workspece
```
**Output:**(cmf_env) /cmf_workspace$
    <br>

Updates the visible current path inside your terminal shell prompt to reflect the new active directory.

---
**Step 5: Copy the Getting Started Example**<br/><br/>
**Description:** Copies the entire starter template folder recursively, matching all nested sub-directories and individual files.

```bash
$  cp -r ../cmf/examples/example-get-started ./example-get-started
```
**Output :**(cmf_env) /cmf_workspace$ 
    <br>
Silently duplicates the target project directory into your current workspace folder without altering the original source files.
    
---
**Step 6: Initialize the Local CMF Repository**<br/><br/>
**Description:** Sets up tracking configuration by linking your local storage path, remote Git repository, and metadata dashboard server.

```bash
$  cmf init local --path /home/user_name/cmf_artifacts --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://localhost:80
```
**Output:** SUCCESS: cmf init complete.
<br>
Prints a single success message confirming that configuration is complete and local metadata tracking is active.

---
**Step 7: Execute the Test Script**<br/><br/>
**Description:** Launches a custom shell script workflow to execute pre-written testing or processing steps.

```bash
$ sh ./test_script.sh
```
**Output:** [5/5] [RUNNING PARSE STEP]
<br>
Streams real-time pipeline status updates directly to the console window, showing current execution step metrics.

---

**Step 8: Retrieves name of  pipeline**<br/><br/>
**Description:** Retrieves a detailed list of all recorded pipelines or components from your CMF server and saves the output directly into a specified file.

```bash
$  cmf pipeline list
```
**Output:** ['Test-env']
<br>

---
**Step 9: Push Metadata to the CMF Server**<br/><br/>
**Description:**  Bundles and uploads the locally recorded tracking data for your specified pipeline run directly to your configured dashboard.

```bash
$  cmf metadata push --pipeline_name name_of_pipeline
```
**Output:** metadata push started<br />
['Test-env/Prepare', 'Test-env/Featurize', 'Test-env/Train', 'Test-env/Evaluate']

<br>
Returns an explicit confirmation string stating that the metadata transfer process has successfully initialized.

---

To learn more about client-side metadata installation, see the Getting Started Tutorial. **[Getting Started Tutorial](../../examples/getting_started)**.