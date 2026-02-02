# Local Storage for Artifact Repository Setup

## Overview
Local storage allows you to use a directory on your local file system as a CMF artifact repository. This is the simplest storage option and is ideal for development, testing, or single-machine workflows where artifacts don't need to be shared across multiple systems.

## Prerequisites
- [cmflib](../setup/index.md#install-cmf-library-ie-cmflib) installed on your system
- A Git repository for tracking your experiment code
- Sufficient disk space in the chosen local directory

## Steps to Set Up Local Storage

### 1. Check CMF Initialization Status

Before setting up local storage, verify whether CMF is already initialized:

```bash
cmf init show
```

If CMF is not initialized, you will see:
```
'cmf' is not configured.
Execute the 'cmf init' command.
```

### 2. Create a Local Directory for Artifacts

Create a directory on your local file system where artifacts will be stored. For example:

```bash
mkdir -p /path/to/local-storage
```

### 3. Initialize CMF with Local Storage

Execute the following command to initialize the local directory as a CMF artifact repository:

**Basic Usage (Required Parameters Only):**
```bash
cmf init local --path /path/to/local-storage \
  --git-remote-url https://github.com/user/experiment-repo.git
```

**With Optional Parameters:**
```bash
cmf init local --path /path/to/local-storage \
  --git-remote-url https://github.com/user/experiment-repo.git \
  --cmf-server-url http://x.x.x.x:80 \
  --neo4j-user neo4j \
  --neo4j-password password \
  --neo4j-uri bolt://localhost:7687
```

**Required Parameters:**

- `--path`: Provide a directory outside of the current working directory which will serve as the artifact repository for artifacts across all the CMF pipelines. This should be an absolute path to your local directory for storing artifacts.
- `--git-remote-url`: Your Git repository URL for version control

**Optional Parameters:**

- `--cmf-server-url`: CMF Server URL (default: http://127.0.0.1:80)
- `--neo4j-user`: Neo4j database username (if using Neo4j for metadata)
- `--neo4j-password`: Neo4j database password
- `--neo4j-uri`: Neo4j connection URI (e.g., bolt://localhost:7687)

### 4. Verify Configuration

After initialization, verify the CMF configuration:

```bash
cmf init show
```

The output should display your local storage configuration, similar to:
```
remote.local-storage.url = /home/user/local-dir
core.remote = local-storage
cmf-server-url = http://127.0.0.1:80
neo4j-user = neo4j
neo4j-password = password
neo4j-uri = bolt://localhost:7687
```

## Using Local Storage

Once configured, you can use CMF commands to manage artifacts:

### Push Artifacts to Local Storage
```bash
cmf artifact push -p 'pipeline-name' -f '/path/to/mlmd-file-name'
```

### Pull Artifacts from Local Storage
```bash
cmf artifact pull -p 'pipeline-name' -f '/path/to/mlmd-file-name' -a 'artifact-name'
```

## Advantages of Local Storage

- **Simple Setup**: No external services or credentials required
- **Fast Access**: Direct file system access provides quick read/write operations
- **Development Friendly**: Ideal for development and testing workflows
- **No Network Dependency**: Works offline without internet connectivity

## Limitations

- **Single Machine**: Artifacts are only accessible from the local machine
- **No Built-in Sharing**: Requires manual file transfer to share artifacts with others
- **Storage Capacity**: Limited by local disk space
- **No Redundancy**: No automatic backup or replication

## When to Use Local Storage

Local storage is suitable for:
- Development and testing environments
- Single-user workflows
- Proof-of-concept projects
- Scenarios where artifacts don't need to be shared across teams
- Learning and exploring CMF features

For production environments or team collaboration, consider using [MinIO S3](./minio-server.md), Amazon S3, or other remote storage options.

