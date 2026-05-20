---
name: cmf-init
description: >
  Use when setting up CMF in a new or existing project. Covers creating a Python
  environment (conda, uv, or venv), installing cmflib (requires Python 3.9–3.11,
  recommended 3.10), running `cmf init` to configure a storage backend (local, S3,
  MinIO, SSH, or OSDF), and verifying the setup.
version: 1.0.0
---

Install cmflib into a Python environment, initialize a storage backend, and verify the setup. If CMF is already initialized, skip to [Verify initialization](#verify-initialization).

## Step 1 — Set up a Python environment

CMF requires **Python 3.9–3.11** (3.10 recommended). Choose the tool you have:

### uv (fastest — install if not present)
```bash
# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv .cmf --python 3.10
source .cmf/bin/activate        # Windows: .cmf\Scripts\activate
```

### conda
```bash
conda create -n cmf python=3.10
conda activate cmf
```
If conda is not installed, use uv or venv instead.

### venv (built-in — always available)
```bash
python3.10 -m venv .cmf
source .cmf/bin/activate        # Windows: .cmf\Scripts\activate
```
If `python3.10` is not found, use `python3 -m venv .cmf` and verify the version with `python --version`.

## Step 2 — Install cmflib

```bash
pip install cmflib
python -c "from cmflib.cmf import Cmf; print('OK')"
```

## Step 3 — Choose a storage backend

| Backend | Use when |
|---------|---------|
| `local` | Single-machine development |
| `minios3` | Shared MinIO server (S3-compatible) |
| `amazons3` | AWS S3 production storage |
| `sshremote` | Artifacts on a remote machine over SSH |
| `osdfremote` | OSDF distributed research data federation |

## Step 4 — Run `cmf init`

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

- **`cmf: command not found`** — ensure the virtual environment is activated; verify with `cmf --version`
- **Wrong Python version** — check with `python --version`; create a new env targeting 3.10 (`uv venv .cmf --python 3.10` or `conda create -n cmf python=3.10`)
- **`python3.10` not found (venv)** — install via system package manager (`sudo apt install python3.10`) or use uv/conda which manage Python versions automatically
- **Git remote error** — CMF requires a configured Git remote; run `git remote add origin <url>` first
- **DVC errors** — CMF uses DVC internally; verify with `dvc --version`; reinstall with `pip install cmflib`
- **MinIO connection refused** — verify the MinIO server is up and `--url` matches the server address and port
- **OSDF token expired or invalid** — CMF validates the token on init and shows issuer, scope, and expiry; regenerate or switch to key-based auth
- **OSDF push fails with permission error** — token may lack write scope for `--path`; contact your OSDF origin administrator

---

**Docs:** [Getting Started](https://hewlettpackard.github.io/cmf/) · [Storage Backends](https://hewlettpackard.github.io/cmf/cmf_client/) · [OSDF Setup](https://hewlettpackard.github.io/cmf/cmf_client/cmf_osdf/) · [Full Tutorial](https://hewlettpackard.github.io/cmf/examples/getting_started/)

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

- **`cmf: command not found`** — run `pip install cmflib`; ensure Python `bin/` is on `PATH`; verify with `cmf --version`
- **Git remote error** — CMF requires a configured Git remote; run `git remote add origin <url>` first
- **DVC errors** — CMF uses DVC internally; verify with `dvc --version`; reinstall with `pip install cmflib`
- **MinIO connection refused** — verify the MinIO server is up and `--url` matches the server address and port
- **OSDF token expired or invalid** — CMF validates the token on init and shows issuer, scope, and expiry; regenerate or switch to key-based auth
- **OSDF push fails with permission error** — token may lack write scope for `--path`; contact your OSDF origin administrator

---

**Docs:** [Getting Started](https://hewlettpackard.github.io/cmf/) · [Storage Backends](https://hewlettpackard.github.io/cmf/cmf_client/) · [OSDF Setup](https://hewlettpackard.github.io/cmf/cmf_client/cmf_osdf/) · [Full Tutorial](https://hewlettpackard.github.io/cmf/examples/getting_started/)
