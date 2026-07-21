# CMF Init Command Reference

## Local storage
```bash
cmf init local \
  --path <dir> \
  --git-remote-url <url> \
  [--cmf-server-url <url>] \
  [--neo4j-user <user> --neo4j-password <pw> --neo4j-uri bolt://localhost:7687]
```

## MinIO (minios3) · [Docs](https://hewlettpackard.github.io/cmf/cmf_client/minio-server/)
```bash
cmf init minios3 \
  --url http://<host>:9000 \
  --endpoint-url http://<host>:9000 \
  --access-key-id <key> \
  --secret-access-key <secret> \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## Amazon S3 (amazons3)
```bash
cmf init amazons3 \
  --url s3://<bucket>/<path> \
  --access-key-id <key> \
  --secret-access-key <secret> \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## SSH remote (sshremote) · [Docs](https://hewlettpackard.github.io/cmf/cmf_client/ssh-setup/)
```bash
cmf init sshremote \
  --path ssh://user@host:/path/to/storage \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## OSDF remote (osdfremote) · [Docs](https://hewlettpackard.github.io/cmf/cmf_client/cmf_osdf/)

### Option 1 — Pre-generated token
```bash
cmf init osdfremote \
  --path <origin-url> \
  --cache <cache-url> \
  --access-token <token-file-or-string> \
  --git-remote-url <url>
```

### Option 2 — Key-based dynamic token
```bash
cmf init osdfremote \
  --path <origin-url> \
  --cache <cache-url> \
  --key-id <id> \
  --key-path <pem-file> \
  --key-issuer <issuer-url> \
  --git-remote-url <url>
```

### Option 3 — Default token location
Place token at `~/.fdp/osdf_token`, then:
```bash
cmf init osdfremote \
  --path <origin-url> \
  --cache <cache-url> \
  --git-remote-url <url>
```

### OSDF parameters

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `--path` | Yes | OSDF origin server URL (writes go here) |
| `--git-remote-url` | Yes | Git repository URL |
| `--cache` | No | OSDF cache/director URL — improves read performance |
| `--access-token` | No* | Pre-generated token file path or value |
| `--key-id` | No* | Key identifier for dynamic token generation |
| `--key-path` | No* | Private key file for dynamic token generation |
| `--key-issuer` | No* | Token issuer URL |

\* Provide `--access-token` OR all three `--key-*` params, or place token at `~/.fdp/osdf_token`.

## Verify
```bash
cmf init show
```

## Python version compatibility

| Python | Status |
|--------|--------|
| 3.10 | **Recommended** |
| 3.11 | Supported |
| 3.9 | Supported (see Ubuntu note below) |
| ≤ 3.8 or ≥ 3.12 | Not supported |

## Environment setup — detailed options · [Docs](https://hewlettpackard.github.io/cmf/setup/#install-cmf-library-ie-cmflib)

### uv (recommended for speed)

```bash
# Install uv (once per machine)
curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
# or: pip install uv

# Create environment with exact Python version
uv venv .cmf --python 3.10

# Activate
source .cmf/bin/activate          # macOS / Linux
.cmf\Scripts\activate             # Windows

# Install CMF
pip install cmflib
```

uv downloads the requested Python version automatically if it is not installed locally — no separate Python installation needed.

### conda

```bash
conda create -n cmf python=3.10
conda activate cmf
pip install cmflib
```

If conda is not installed, download [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (minimal) or [Anaconda](https://www.anaconda.com/download) (full). Alternatively use uv or venv.

### venv (built-in, no extras needed)

```bash
# Linux / macOS — use the specific Python binary
python3.10 -m venv .cmf
source .cmf/bin/activate

# Windows
py -3.10 -m venv .cmf
.cmf\Scripts\activate

pip install cmflib
```

If `python3.10` is not available, install it via your system package manager:
```bash
# Ubuntu / Debian
sudo apt install python3.10 python3.10-venv

# macOS (Homebrew)
brew install python@3.10

# Windows — download from python.org
```

Or switch to uv/conda, which manage Python versions for you.

## Guided walkthrough (new projects)

Full end-to-end setup from scratch with local storage, using uv:

```bash
# 1. Create a working directory and initialize Git
mkdir my-ml-project && cd my-ml-project
git init
git remote add origin https://github.com/your-org/your-repo.git

# 2. Set up Python environment
uv venv .cmf --python 3.10
source .cmf/bin/activate    # Windows: .cmf\Scripts\activate

# 3. Install CMF
pip install cmflib

# 4. Create a local artifact directory (outside the repo is fine)
mkdir -p ~/cmf-artifacts

# 5. Initialize CMF
cmf init local \
  --path ~/cmf-artifacts \
  --git-remote-url https://github.com/your-org/your-repo.git

# 6. Confirm
cmf init show
```

The `mlmd` file appears only after the first instrumented pipeline run — not after `cmf init`.

## Python 3.9 on Ubuntu — known issue

If you encounter `ModuleNotFoundError: No module named 'distutils.cmd'`:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt install python3.9 python3.9-dev python3.9-distutils python3.9-venv
```

Use Python 3.10 to avoid this entirely.

## References

- [Installing cmflib](https://hewlettpackard.github.io/cmf/setup/#install-cmf-library-ie-cmflib)
- [MinIO server setup](https://hewlettpackard.github.io/cmf/cmf_client/minio-server/)
- [SSH remote setup](https://hewlettpackard.github.io/cmf/cmf_client/ssh-setup/)
- [OSDF remote setup](https://hewlettpackard.github.io/cmf/cmf_client/cmf_osdf/)
