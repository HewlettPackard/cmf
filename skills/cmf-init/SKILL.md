---
name: cmf-init
description: >
  Use when setting up CMF in a new or existing project. Covers installing cmflib,
  running `cmf init` to configure a storage backend (local, S3, MinIO, SSH, or OSDF),
  creating the mlmd metadata store, and verifying the setup. Works for both first-time
  users and engineers setting up a new environment.
version: 1.0.0
---

Initialize CMF in the user's project. Detect what they have, guide them through `cmf init`, and verify the setup ends with a working `mlmd` file.

## Prerequisites

- Python 3.9–3.11 (3.10 recommended)
- Git repository initialized (`git init` if needed)
- A storage backend available — see detection below

## Step 1 — Install cmflib

```bash
pip install cmflib
```

Verify:

```bash
cmf --version
python -c "from cmflib.cmf import Cmf; print('OK')"
```

## Step 2 — Detect storage backend

Ask the user which backend they want, or detect from their environment:

| Backend | When to use |
|---------|------------|
| `local` | Development on a single machine; artifacts stored in a local directory |
| `minios3` | Team shares a MinIO server; S3-compatible object storage |
| `amazons3` | Production; artifacts stored in AWS S3 |
| `sshremote` | Artifacts stored on a remote machine over SSH |
| `osdfremote` | Distributed research data federation (OSDF / Pelican Platform) across institutions |

## Step 3 — Run `cmf init`

### Local storage (quickstart)

```bash
cmf init local \
  --path /path/to/local-artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git
```

Optional: add CMF Server and Neo4j graph layer:

```bash
cmf init local \
  --path /path/to/local-artifact-storage \
  --git-remote-url https://github.com/your-org/your-repo.git \
  --cmf-server-url http://<server-ip>:80 \
  --neo4j-user neo4j \
  --neo4j-password password \
  --neo4j-uri bolt://localhost:7687
```

### MinIO / S3

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

### OSDF remote (Open Science Data Federation)

OSDF is a distributed data federation backed by the [Pelican Platform](https://pelicanplatform.org/), designed for sharing artifacts across institutions and national research compute pools.

First confirm CMF is initialized (`cmf init show`), then choose one of three authentication options:

**Option 1 — Pre-generated token (recommended):**
```bash
cmf init osdfremote \
  --path https://fdp-origin.labs.hpe.com:8443/fdp-hpe/cmf_test \
  --cache https://osdf-director.osg-htc.org/ \
  --access-token ~/.fdp/osdf_token \
  --git-remote-url https://github.com/your-org/your-repo.git
```

**Option 2 — Key-based dynamic token generation:**
```bash
cmf init osdfremote \
  --path https://fdp-origin.labs.hpe.com:8443/fdp-hpe/cmf_test \
  --cache https://osdf-director.osg-htc.org/ \
  --key-id XXXX \
  --key-path ~/private_hpe.pem \
  --key-issuer https://t.nationalresearchplatform.org/fdp-hpe \
  --git-remote-url https://github.com/your-org/your-repo.git
```

**Option 3 — Default token location** (token stored at `~/.fdp/osdf_token`, no explicit flag needed):
```bash
cmf init osdfremote \
  --path https://fdp-origin.labs.hpe.com:8443/fdp-hpe/cmf_test \
  --cache https://osdf-director.osg-htc.org/ \
  --git-remote-url https://github.com/your-org/your-repo.git
```

**OSDF parameters:**

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `--path` | Yes | OSDF origin server URL (writes go here) |
| `--git-remote-url` | Yes | Git repository URL for version control |
| `--cache` | No | OSDF cache/director URL — improves read performance |
| `--access-token` | No* | Pre-generated token file path or plain text |
| `--key-id` | No* | Key identifier for dynamic token generation |
| `--key-path` | No* | Private key file for dynamic token generation |
| `--key-issuer` | No* | Token issuer URL for dynamic token generation |

\* Provide either `--access-token` OR all three `--key-*` parameters, or place the token at `~/.fdp/osdf_token`.

CMF validates the token automatically before push/pull and displays its issuer, scope, and expiry.

## Step 4 — Verify initialization

```bash
cmf init show
```

Expected output shows the configured DVC remote, Git remote URL, and (optionally) CMF Server URL.

## Step 5 — Confirm the mlmd file is created

The `mlmd` file appears after the first pipeline run. It is created automatically when your instrumented code first calls `Cmf(filepath="mlmd", ...)`. It does **not** exist after `cmf init` alone.

## Quick reference card

| Command | Purpose |
|---------|---------|
| `cmf init local --path <dir> --git-remote-url <url>` | Init with local storage |
| `cmf init minios3 ...` | Init with MinIO / S3 backend |
| `cmf init amazons3 ...` | Init with Amazon S3 |
| `cmf init sshremote --path ssh://user@host:/path ...` | Init with SSH remote |
| `cmf init osdfremote --path <origin-url> ...` | Init with OSDF storage |
| `cmf init show` | Show current configuration |
| `cmf init --help` | All init options |

## Guided walkthrough (new users)

1. Create a working directory and initialize Git:
   ```bash
   mkdir my-ml-project && cd my-ml-project
   git init
   git remote add origin https://github.com/your-org/your-repo.git
   ```

2. Install CMF:
   ```bash
   pip install cmflib
   ```

3. Create a local artifact directory (outside the repo is fine):
   ```bash
   mkdir -p ~/cmf-artifacts
   ```

4. Initialize CMF:
   ```bash
   cmf init local --path ~/cmf-artifacts --git-remote-url https://github.com/your-org/your-repo.git
   ```

5. Confirm with `cmf init show` — you should see the DVC remote and Git URL.

6. Now instrument your pipeline code. See the **cmf-instrument** skill.

## Troubleshooting

- **`cmf: command not found`** — run `pip install cmflib` and ensure your Python `bin` directory is on `PATH`
- **`git remote` error** — `cmf init` requires a configured Git remote; add one with `git remote add origin <url>`
- **DVC errors** — CMF uses DVC internally; if DVC is not installed, `pip install cmflib` should include it; check with `dvc --version`
- **MinIO connection refused** — verify the MinIO server is running and the `--url` matches the server address and port
- **OSDF token expired or invalid** — CMF validates the token on init; regenerate the token or use key-based auth. Check expiry with `cmf init show`
- **OSDF push fails with permission error** — the token may lack write scope for the configured `--path`. Contact your OSDF origin administrator

## Further reading

- `docs/cmf_client/index.md` — Full CMF Client CLI guide
- `docs/cmf_client/local-storage-setup.md` — Local storage details
- `docs/cmf_client/minio-server.md` — MinIO backend setup
- `docs/cmf_client/ssh-setup.md` — SSH remote setup
- `docs/cmf_client/cmf_osdf.md` — OSDF remote setup and token authentication
