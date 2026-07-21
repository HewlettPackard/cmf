# CMF Sync CLI Reference

## Metadata commands

| Command | Flags | Purpose |
|---------|-------|---------|
| `cmf metadata push` | `-p <pipeline>` | Upload local mlmd → CMF Server |
| `cmf metadata pull` | `-p <pipeline>` | Download metadata from CMF Server |
| `cmf metadata export` | `-p <pipeline> -f <file>` | Export metadata to JSON/CSV |

## Artifact commands

| Command | Flags | Purpose |
|---------|-------|---------|
| `cmf artifact push` | `-p <pipeline>` | Upload artifacts → storage backend (S3/MinIO/SSH/OSDF/local) |
| `cmf artifact pull` | `-p <pipeline>` | Download artifacts from storage |
| `cmf artifact list` | `-p <pipeline>` | List tracked artifacts |

## Repo commands

| Command | Purpose |
|---------|---------|
| `cmf repo push` | Push Git repo + DVC artifact pointers |
| `cmf repo pull` | Pull Git repo + DVC artifact pointers |

## Query commands

| Command | Flags | Purpose |
|---------|-------|---------|
| `cmf pipeline list` | — | List all local pipelines |
| `cmf execution list` | `-p <pipeline>` | List executions for a pipeline |
