# CMF Client Installation Guide

This page covers the step-by-step setup of `cmflib` on client nodes to track and log machine learning pipeline metadata.

## Prerequisites

### 1. Configure Git Setup
CMF uses Git for code versioning and tracking local code changes. Configure your Git identity before using CMF:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 2. Configure Artifact Storage
Ensure you have access credentials and network pathways ready for your chosen artifact repository:
- **Storage Backend**: [local](./../cmf_client/local-storage-setup.md), S3, [MinIOS3](./../cmf_client/minio-server.md), [ssh storage](./../cmf_client/ssh-setup.md) or [OSDF](./../cmf_client/cmf_osdf.md) storage for artifacts.

---

# CLI Execution Reference
Before initiating the environment setup, review the foundational commands required to deploy the client.
Please follow the mandatory installation and setup guide before proceeding. [Installation and Setup](../../setup/#cli-execution-reference).

## Installation Steps

**Open new terminal and start the execution of commands:**<br/><br/> 
**Step 1: Verify the CMF Package Installation**<br/><br/>
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
**Step 2: Locate the CMF Executable Path**<br/><br/>
**Description:** Searches your system's environmental path variable to find the exact file location of the cmf command tool.

```bash
$  which cmf
```
**Output:**/home/user_name/cmf_env/bin/cmf
<br>

Returns the absolute directory path pointing directly to the binary executable inside your active environment.

---
**Step 3: Navigate to the CMF Workspace**<br/><br/>
**Description:** Changes your terminal's current working directory context to the specific folder named cmf_workspace.

```bash
$  cd cmf_workspece
```
**Output:**(cmf_env) /cmf_workspace$
    <br>

Updates the visible current path inside your terminal shell prompt to reflect the new active directory.

---
**Step 4: Copy the Getting Started Example**<br/><br/>
**Description:** Copies the entire starter template folder recursively, matching all nested sub-directories and individual files.

```bash
$  cp -r ../cmf/examples/example-get-started ./example-get-started
```
**Output :**(cmf_env) /cmf_workspace$ 
    <br>
Silently duplicates the target project directory into your current workspace folder without altering the original source files.
    
---
**Step 5: Initialize the Local CMF Repository**<br/><br/>
**Description:** Sets up tracking configuration by linking your local storage path, remote Git repository, and metadata dashboard server.

```bash
$  cmf init local --path /home/user_name/cmf_artifacts --git-remote-url https://github.com/user/experiment-repo.git --cmf-server-url http://localhost:80
```
**Output:** SUCCESS: cmf init complete.
<br>
Prints a single success message confirming that configuration is complete and local metadata tracking is active.

---
**Step 6: Execute the Test Script**<br/><br/>
**Description:** Launches a custom shell script workflow to execute pre-written testing or processing steps.

```bash
$ sh ./test_script.sh
```
**Output:** [5/5] [RUNNING PARSE STEP]
<br>
Streams real-time pipeline status updates directly to the console window, showing current execution step metrics.

---

**Step 7: Retrieves name of  pipeline**<br/><br/>
**Description:** Retrieves a detailed list of all recorded pipelines or components from your CMF server and saves the output directly into a specified file.

```bash
$  cmf pipeline list
```
**Output:** ['Test-env']
<br>

---
**Step 8: Push Metadata to the CMF Server**<br/><br/>
**Description:**  Bundles and uploads the locally recorded tracking data for your specified pipeline run directly to your configured dashboard.

```bash
$  cmf metadata push --pipeline_name name_of_pipeline
```
**Output:** metadata push started<br />
........................................
{'message': "File 'cmf_artifacts/python_env_7a33cef7ba87f7aa722722f974fc6e6e.txt' uploaded successfully"}<br />
{'message': "File '13e556fa36c8a2a1f711be954edaa805' already exists at /cmf-server/data/labels. Skipping upload."}<br />
SUCCESS: ./mlmd is successfully pushed.

<br>

---

To learn more about client-side metadata installation, see the Getting Started Tutorial. **[Getting Started Tutorial](../../examples/getting_started)**.