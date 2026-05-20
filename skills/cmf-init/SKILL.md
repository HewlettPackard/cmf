---
name: cmf-init
description: >
  Use when setting up CMF in a new or existing project. Covers creating a Python
  environment (conda, uv, or venv), installing cmflib (requires Python 3.9–3.11,
  recommended 3.10), running `cmf init` to configure a storage backend (local, S3,
  MinIO, SSH, or OSDF), and verifying the setup. Linux only — cmflib does not support macOS.
version: 1.0.0
---

> **macOS is not supported.** cmflib does not install or run on macOS. See open issues
> [#185](https://github.com/HewlettPackard/cmf/issues/185) and
> [#263](https://github.com/HewlettPackard/cmf/issues/263) for status.
> Use a Linux machine or a Linux VM/container instead.

Install cmflib into a Python environment, initialize a storage backend, and verify the setup. If CMF is already initialized, skip to [Verify initialization](#verify-initialization).

## Step 1 — Set up a Python environment

CMF requires **Python 3.9–3.11** (3.10 recommended).

Detect available tools and ask the user which they prefer:

```bash
which uv && echo "uv available" || echo "uv not found"
which conda && echo "conda available" || echo "conda not found"
# venv is always available via Python's standard library
```

| Tool | Priority | Command |
|------|----------|---------|
| **uv** | Preferred — offer to install if missing | `uv venv .cmf --python 3.10 && source .cmf/bin/activate` |
| **conda** | Next — use if uv unavailable | `conda create -n cmf python=3.10 && conda activate cmf` |
| **venv** | Always available fallback | `python3.10 -m venv .cmf && source .cmf/bin/activate` |

If **uv is not installed**, offer to install it (manages Python versions automatically):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux
# or: pip install uv
```

If **none of the above** apply, skip environment creation and install directly with `pip install cmflib` (requires system Python 3.9–3.11).

See [references/init-commands.md](references/init-commands.md#environment-setup--detailed-options) for full OS-specific setup and a guided walkthrough.

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
Three authentication options — see [references/init-commands.md](references/init-commands.md#osdf-remote-osdfremote) for full parameter table.

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

- **macOS** — cmflib is not supported; use Linux or a Linux container
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
