# CMF Init Command Reference

## Local storage
```bash
cmf init local \
  --path <dir> \
  --git-remote-url <url> \
  [--cmf-server-url <url>] \
  [--neo4j-user <user> --neo4j-password <pw> --neo4j-uri bolt://localhost:7687]
```

## MinIO (minios3)
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

## SSH remote (sshremote)
```bash
cmf init sshremote \
  --path ssh://user@host:/path/to/storage \
  --git-remote-url <url> \
  [--cmf-server-url <url>]
```

## OSDF remote (osdfremote)

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

## Guided walkthrough (new projects)

Full end-to-end setup from scratch with local storage:

```bash
# 1. Create a working directory and initialize Git
mkdir my-ml-project && cd my-ml-project
git init
git remote add origin https://github.com/your-org/your-repo.git

# 2. Install CMF
pip install cmflib

# 3. Create a local artifact directory (outside the repo is fine)
mkdir -p ~/cmf-artifacts

# 4. Initialize CMF
cmf init local \
  --path ~/cmf-artifacts \
  --git-remote-url https://github.com/your-org/your-repo.git

# 5. Confirm
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

Python 3.10 is recommended to avoid this.
