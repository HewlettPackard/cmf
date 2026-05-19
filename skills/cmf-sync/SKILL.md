---
name: cmf-sync
description: >
  Use when pushing or pulling CMF metadata and artifacts between a local environment and
  a CMF Server or central artifact repository. Covers `cmf metadata push/pull`,
  `cmf artifact push/pull`, `cmf repo push/pull`, and collaborative team workflows.
  Assumes CMF has already been initialized with `cmf init`.
version: 1.0.0
---

Help the user sync their CMF metadata and artifacts with the central CMF Server and artifact storage. Detect their workflow (solo vs. team, first push vs. update) and guide them to the right commands.

## Prerequisites

- CMF initialized (`cmf init show` shows a valid configuration)
- At least one pipeline run completed (an `mlmd` file exists)
- CMF Server running and reachable at the URL shown in `cmf init show`

## Workflow overview

```
Local environment                CMF Server / Artifact Storage
─────────────────                ─────────────────────────────
mlmd (metadata)      ──push──►   CMF Server database
artifacts (data/models) ──push──►  S3 / MinIO / SSH / local storage
                     ◄──pull──   (teammates pull metadata + artifacts)
```

## Push workflow

Run these after every pipeline execution to share your results:

### 1. Push metadata to CMF Server

```bash
cmf metadata push -p <pipeline_name>
```

Example:

```bash
cmf metadata push -p "my_pipeline"
```

This sends the contents of the local `mlmd` file for the named pipeline to the CMF Server.

### 2. Push artifacts to artifact storage

```bash
cmf artifact push -p <pipeline_name>
```

Example:

```bash
cmf artifact push -p "my_pipeline"
```

This uploads all artifacts tracked in the pipeline (datasets, models, metrics files) to the configured storage backend (S3, MinIO, SSH, local).

### 3. Push code to Git (optional, if not done automatically)

```bash
cmf repo push
```

Pushes the Git repository (code + DVC-tracked artifact pointers) to the configured Git remote.

## Pull workflow

Run these when you want to get a teammate's results or reproduce an experiment:

### 1. Pull metadata from CMF Server

```bash
cmf metadata pull -p <pipeline_name>
```

### 2. Pull artifacts from storage

```bash
cmf artifact pull -p <pipeline_name>
```

### 3. Pull Git repo (code + DVC pointers)

```bash
cmf repo pull
```

## Exporting metadata

Export pipeline metadata to a CSV or JSON file for offline analysis:

```bash
cmf metadata export -p <pipeline_name> -f metadata_export.json
```

## End-to-end collaborative workflow

**Developer A (runs experiments and shares results):**

```bash
# 1. Run the pipeline
python src/train.py

# 2. Push metadata so the team can see the results
cmf metadata push -p "my_pipeline"

# 3. Push artifacts so teammates can reproduce
cmf artifact push -p "my_pipeline"
```

**Developer B (picks up the shared work):**

```bash
# 1. Pull the metadata to see pipelines and executions
cmf metadata pull -p "my_pipeline"

# 2. Pull artifacts needed to continue
cmf artifact pull -p "my_pipeline"

# 3. Resume work (e.g. run the next pipeline stage)
python src/evaluate.py
```

## Quick reference

| Command | Purpose |
|---------|---------|
| `cmf metadata push -p <name>` | Upload local mlmd → CMF Server |
| `cmf metadata pull -p <name>` | Download metadata from CMF Server → local mlmd |
| `cmf metadata export -p <name> -f <file>` | Export metadata to a file |
| `cmf artifact push -p <name>` | Upload artifacts → storage backend |
| `cmf artifact pull -p <name>` | Download artifacts from storage |
| `cmf repo push` | Push Git repo + DVC pointers |
| `cmf repo pull` | Pull Git repo + DVC pointers |
| `cmf pipeline list` | List all local pipelines |
| `cmf execution list -p <name>` | List executions for a pipeline |
| `cmf artifact list -p <name>` | List artifacts for a pipeline |

## Troubleshooting

- **`Connection refused` on metadata push**: CMF Server is not running or the URL in `cmf init show` is wrong. Start the server or re-run `cmf init` with the correct `--cmf-server-url`.
- **`DVC remote not configured`**: Run `cmf init` again with the correct storage backend arguments.
- **`Pipeline not found`**: The `-p` flag must match the `pipeline_name` used in `Cmf(pipeline_name=...)`. Check with `cmf pipeline list`.
- **Partial push**: If a push is interrupted, re-run the same command — CMF only uploads missing artifacts.
- **`mlmd file not found`**: Run at least one instrumented pipeline stage before pushing metadata.

## Further reading

- `docs/cmf_client/index.md` — Full CLI guide with collaborative workflow examples
- `docs/cmf_client/cmf_client_commands.md` — Complete command reference
- `docs/setup/index.md` — CMF Server installation instructions
