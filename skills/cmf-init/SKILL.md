---
name: cmf-init
description: >
  Use when setting up CMF in a new or existing project. Covers installing cmflib,
  running `cmf init` to configure a storage backend (local, S3, MinIO, SSH, or OSDF),
  creating the mlmd metadata store, and verifying the setup.
version: 1.0.0
---

Install cmflib, initialize a storage backend, and verify the setup. If CMF is already initialized, skip to [Verify initialization](#verify-initialization).

## Step 1 — Install cmflib

```bash
pip install cmflib
python -c "from cmflib.cmf import Cmf; print('OK')"
```

## Step 2 — Choose a storage backend

| Backend | Use when |
|---------|---------|
| `local` | Single-machine development |
| `minios3` | Shared MinIO server (S3-compatible) |
| `amazons3` | AWS S3 production storage |
| `sshremote` | Artifacts on a remote machine over SSH |
| `osdfremote` | OSDF distributed research data federation |

## Step 3 — Run `cmf init`

### Local
```bash
cmf init local \
  --path /path/to/artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git
```
Optional: add `--cmf-server-url http://<server>:80` to point at a shared CMF Server.

### MinIO / Amazon S3
```bash
# MinIO
cmf init minios3 \
  --url http://<minio-host>:9000 \
  --endpoint-url http://<minio-host>:9000 \
  --access-key-id <key> \
  --secret-access-key <secret> \
  --git-remote-url https://github.com/your-org/your-repo.git

# Amazon S3
cmf init amazons3 \
  --url s3://your-bucket/path \
  --access-key-id <key> \
  --secret-access-key <secret> \
  --git-remote-url https://github.com/your-org/your-repo.git
```

### SSH remote
```bash
cmf init sshremote \
  --path ssh://user@host:/path/to/storage \
  --git-remote-url https://github.com/your-org/your-repo.git
```

### OSDF remote
Three authentication options — see [references/init-commands.md](references/init-commands.md#osdf-remote) for full parameter table.

**Option 1 — pre-generated token (recommended):**
```bash
cmf init osdfremote \
  --path https://fdp-origin.labs.hpe.com:8443/fdp-hpe/cmf_test \
  --cache https://osdf-director.osg-htc.org/ \
  --access-token ~/.fdp/osdf_token \
  --git-remote-url https://github.com/your-org/your-repo.git
```

## Verify initialization

```bash
cmf init show   # should display remote, git URL, and optional server URL
```

The `mlmd` file is created automatically on the first pipeline run, not by `cmf init` itself.

## Troubleshooting

- **`cmf: command not found`** — run `pip install cmflib`; ensure Python `bin/` is on `PATH`
- **Git remote error** — add a remote first: `git remote add origin <url>`
- **OSDF token expired** — regenerate token or switch to key-based auth
- **MinIO connection refused** — verify the MinIO server is up and `--url` matches

---

**Docs:** [Getting Started](https://hewlettpackard.github.io/cmf/) · [Storage Backends](https://hewlettpackard.github.io/cmf/cmf_client/) · [OSDF Setup](https://hewlettpackard.github.io/cmf/cmf_client/cmf_osdf/) · [Full Tutorial](https://hewlettpackard.github.io/cmf/examples/getting_started/)
