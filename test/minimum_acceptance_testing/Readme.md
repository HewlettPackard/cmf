# MAT Framework (Minimum Acceptance Testing)

## Description

The MAT framework validates the essential functionality of cmf before a PR is merged.
It covers cmf-client interactions and cmf-server API endpoints.
All tests are discovered and run automatically by pytest from a single command.

## Structure

```
test/minimum_acceptance_testing/
├── conftest.py              # Shared: cmf_server_url injected from config.json
├── config.json              # Environment config: server URL, local path
├── client/
│   ├── conftest.py          # Client fixtures: workspace setup, server start/stop
│   └── test_local.py        # cmf init local + artifact/metadata push/pull
└── server/
    ├── conftest.py          # Skips server tests at runtime if cmf-server is not reachable
    └── test_api_endpoints.py  # cmf-server REST API validation (HTTP calls to live server)
```

## Installation

### Install [cmf](../../docs/index.md#installation)

### Install test dependencies
```bash
pip install -r requirements.txt
pip install -r server/requirements.txt
```

## Configuration

Edit `test/minimum_acceptance_testing/config.json`:
```json
{
    "cmf_server_url": "http://x.x.x.x:80",
    "local_path": "/home/user/local-storage"
}
```

Edit `docker-compose-server.yml` volumes to point to your test data directory:
```yaml
volumes:
   - /home/hpe-user/cmf/test/cmf-server/data:/cmf-server/data
   - /home/hpe-user/cmf/test/cmf-server/data/static:/cmf-server/data/static
```

## Running Tests

### Run the full MAT suite (client + server)
```bash
cd cmf
python -m pytest test/minimum_acceptance_testing/ -v -s
```
> `cmf_server_url` is read automatically from `config.json`. No CLI flag needed.
> If the server is not running, the framework starts it automatically via docker compose and stops it after all tests finish.
> If the server is already running, it is reused and left running after tests.

### Run only client tests
```bash
python -m pytest test/minimum_acceptance_testing/client/ -v
```

### Run only server API tests
> Requires cmf-server to be running at the `cmf_server_url` in `config.json`.
```bash
python -m pytest test/minimum_acceptance_testing/server/ -v
```

## What is Tested

### cmf-client tests (`client/test_local.py`)
1. `test_cmf_init_show` — show current init configuration
2. `test_cmf_init_local` — initialize a local repository
3. `test_script` — execute sample pipeline script (`test_script.sh`)
4. `test_artifact_push` — push artifacts to local storage
5. `test_metadata_push` — push metadata to cmf-server
6. `test_metadata_pull` — pull metadata from cmf-server
7. `test_artifact_pull` — pull all artifacts
8. `test_artifact_pull_single` — pull a specific artifact by name

### cmf-server API tests (`server/test_api_endpoints.py`)
> Tests make HTTP calls to the live running server — no local Postgres connection required.
> Server tests are automatically skipped if cmf-server is not reachable at runtime.

1. `test_read_root` — `GET /` server health check
2. `test_display_pipelines` — `GET /api/pipelines` retrieve all pipeline names
3. `test_display_artifact_types` — `GET /api/artifact_types` retrieve artifact types
4. `test_display_pipeline_stages` — `GET /api/pipeline-stages/{pipeline}` retrieve pipeline stages
5. `test_display_executions` — `GET /api/executions-by-stage/{pipeline}` retrieve executions per stage
6. `test_display_artifact_types_by_stage` — `GET /api/artifact-types-by-stage/{pipeline}` retrieve artifact types per stage
7. `test_display_artifacts` — `GET /api/artifacts-by-stage/{pipeline}` retrieve artifacts per stage and type
