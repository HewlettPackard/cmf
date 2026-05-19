---
name: cmf-sync
description: >
  Use when pushing or pulling CMF metadata and artifacts between a local environment and
  a CMF Server or central artifact repository (S3, MinIO, SSH, OSDF, local). Covers
  `cmf metadata push/pull`, `cmf artifact push/pull`, `cmf repo push/pull`, and
  collaborative team workflows. Assumes `cmf init` has been run.
version: 1.0.0
---

Help the user sync their metadata and artifacts. Detect whether they are pushing (sharing results) or pulling (getting a teammate's work).

## Prerequisites

- `cmf init show` returns a valid configuration
- At least one pipeline run completed (an `mlmd` file exists)
- CMF Server reachable at the URL in `cmf init show`

## Push workflow (after running your pipeline)

```bash
cmf metadata push -p my_pipeline    # upload mlmd → CMF Server
cmf artifact push -p my_pipeline    # upload artifacts → S3/MinIO/SSH/OSDF/local
```

## Pull workflow (get a teammate's results)

```bash
cmf metadata pull -p my_pipeline    # download metadata from CMF Server
cmf artifact pull -p my_pipeline    # download artifacts from storage backend
```

## Code + DVC pointer sync

```bash
cmf repo push   # push Git repo + DVC pointers
cmf repo pull   # pull Git repo + DVC pointers
```

## Metadata export

```bash
cmf metadata export -p my_pipeline -f export.json
```

## End-to-end collaborative example

**Developer A — share results:**
```bash
python src/train.py
cmf metadata push -p my_pipeline
cmf artifact push -p my_pipeline
```

**Developer B — pick up the work:**
```bash
cmf metadata pull -p my_pipeline
cmf artifact pull -p my_pipeline
python src/evaluate.py
```

## List what's tracked

```bash
cmf pipeline list
cmf execution list -p my_pipeline
cmf artifact list -p my_pipeline
```

See [references/cli-commands.md](references/cli-commands.md) for the full command flag reference.

## Troubleshooting

- **`Connection refused` on push** — CMF Server is not running or the URL in `cmf init show` is wrong
- **`Pipeline not found`** — the `-p` value must match `pipeline_name` used in `Cmf(...)`. Check with `cmf pipeline list`
- **Partial push** — re-run the same command; CMF only uploads missing artifacts
- **`mlmd file not found`** — run at least one instrumented pipeline stage before pushing

---

**Docs:** [CMF Client Guide](https://hewlettpackard.github.io/cmf/cmf_client/) · [CLI Command Reference](https://hewlettpackard.github.io/cmf/cmf_client/cmf_client_commands/)
