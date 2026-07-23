# MAT Framework (Minimum Acceptance Testing)

## Description

The MAT framework validates the essential functionality of CMF before a PR is merged.
It covers all five cmf-client storage backends and cmf-server API endpoints.
All tests are discovered and run automatically by pytest from a single command.

## Structure

```
test/minimum_acceptance_testing/
├── conftest.py                   # Shared: injects cmf_server_url from config.json into every test
├── config.json                   # All runtime credentials and URLs for every backend
├── _helpers.py                   # assert_cmf_success() — detects CMF failure return strings
├── client/
│   ├── conftest.py               # Workspace setup, cmf-server auto-start/stop fixtures
│   ├── test_local.py             # Local storage backend tests
│   ├── test_minios3.py           # MinioS3 backend tests
│   ├── test_amazons3.py          # Amazon S3 backend tests
│   ├── test_sshremote.py         # SSH remote backend tests
│   └── test_osdf.py              # OSDF remote backend tests
└── server/
    ├── conftest.py               # Skips server tests if cmf-server is not reachable
    └── test_api_endpoints.py     # cmf-server REST API validation (HTTP calls to live server)
```

## Prerequisites

### 1. Install CMF
Follow the [CMF installation guide](../../docs/index.md#installation).

### 2. Install test dependencies
```bash
cd cmf
pip install -r test/minimum_acceptance_testing/requirements.txt
```

### 3. Start required external services

#### cmf-server
The MAT framework will **automatically start** cmf-server via docker compose if it is not already running, and stop it when all tests finish. If it is already running, it is reused and left running after tests.

If you prefer to start it manually before running tests:
```bash
cd cmf
docker compose -f docker-compose-server.yml up -d
```

#### MinioS3 server (required only for `test_minios3.py`)
The MinioS3 server is **NOT started automatically** by the MAT framework. You must start it yourself before running the MinioS3 tests:
```bash
cd cmf
docker start <your-minio-container>
# or
docker compose up -d minio
```
Verify it is running:
```bash
curl -s http://<minio-host>:9000 | head -1
```
> If MinioS3 is not running, `test_artifact_push`, `test_artifact_pull`, and `test_artifact_pull_single` will correctly FAIL with a connection error.

---

## Configuration

Edit `test/minimum_acceptance_testing/config.json` with your environment values:

```json
{
    "cmf_server_url": "http://<host>:80",

    "local_path": "/path/to/local-storage",

    "minio_url": "s3://<bucket-name>",
    "minio_endpoint_url": "http://<minio-host>:9000",
    "minio_access_key_id": "<access-key>",
    "minio_secret_key": "<secret-key>",

    "aws_url": "s3://<bucket-name>",
    "aws_access_key_id": "<aws-access-key-id>",
    "aws_secret_key": "<aws-secret-key>",
    "aws_session_token": "<aws-session-token>",

    "ssh_path": "ssh://<host>/path/to/storage",
    "ssh_user": "<username>",
    "ssh_port": "22",
    "ssh_password": "<password>",

    "osdf_path": "https://<osdf-origin>/repo",
    "osdf_cache": "https://<osdf-director>/",
    "osdf_access_token": "~/.fdp/osdf_token"
}
```

**Required fields per backend:**

| Backend | Required config keys |
|---|---|
| Local | `cmf_server_url`, `local_path` |
| MinioS3 | `cmf_server_url`, `minio_url`, `minio_endpoint_url`, `minio_access_key_id`, `minio_secret_key` |
| AmazonS3 | `cmf_server_url`, `aws_url`, `aws_access_key_id`, `aws_secret_key`, `aws_session_token` |
| SSH remote | `cmf_server_url`, `ssh_path`, `ssh_user`, `ssh_password` |
| OSDF | `cmf_server_url`, `osdf_path`, `osdf_cache`, `osdf_access_token` |

> If any required field is empty, `test_cmf_init_<backend>` will immediately FAIL with:
> `config.json: '<key>' is not set. Required for <backend> backend.`
> All downstream tests in that module will then fail with `'cmf' is not configured.`

---

## Running Tests

### Run the full MAT suite (all backends + server)
```bash
cd cmf
python -m pytest test/minimum_acceptance_testing/ -v
```

### Run a single backend
```bash
# Local storage
python -m pytest test/minimum_acceptance_testing/client/test_local.py -v

# MinioS3
python -m pytest test/minimum_acceptance_testing/client/test_minios3.py -v

# Amazon S3
python -m pytest test/minimum_acceptance_testing/client/test_amazons3.py -v

# SSH remote
python -m pytest test/minimum_acceptance_testing/client/test_sshremote.py -v

# OSDF
python -m pytest test/minimum_acceptance_testing/client/test_osdf.py -v
```

### Run only server API tests
```bash
python -m pytest test/minimum_acceptance_testing/server/ -v
```
> Server tests are automatically skipped if cmf-server is not reachable at the configured URL.

### Run only client tests (all backends)
```bash
python -m pytest test/minimum_acceptance_testing/client/ -v
```

---

## Test Order (all backends follow the same sequence)

Each backend module runs 8 tests in this fixed order:

| # | Test | What it does |
|---|---|---|
| 1 | `test_cmf_init_<backend>` | Initializes CMF with the backend credentials from config.json |
| 2 | `test_cmf_init_show` | Displays the current CMF configuration |
| 3 | `test_script` | Runs `test_script.sh` to create the sample pipeline and `mlmd` file |
| 4 | `test_metadata_push` | Pushes `mlmd` metadata to cmf-server |
| 5 | `test_metadata_pull` | Pulls metadata from cmf-server into `mlmd_pull` |
| 6 | `test_artifact_push` | Pushes artifacts to the configured remote storage |
| 7 | `test_artifact_pull` | Pulls all artifacts from remote storage |
| 8 | `test_artifact_pull_single` | Pulls a single artifact (`data.xml.gz`) from remote storage |

---

## Server API Tests (`server/test_api_endpoints.py`)

Tests make HTTP calls to the live running cmf-server. No direct Postgres connection is required.

| Test | Endpoint |
|---|---|
| `test_read_root` | `GET /` |
| `test_display_pipelines` | `GET /api/pipelines` |
| `test_display_artifact_types` | `GET /api/artifact_types` |
| `test_display_executions` | `GET /api/executions-by-stage/{pipeline}` |
| `test_display_artifacts` | `GET /api/artifacts-by-stage/{pipeline}` |

