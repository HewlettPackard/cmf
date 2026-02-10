# OSDF Backend Testing

This directory contains tests for the OSDF (Open Science Data Federation) storage backend for CMF.

## Test Coverage

The OSDF test suite (`test_osdf.py`) covers:

### Functional Tests
1. **Initialization** - CMF initialization with OSDF backend (token and key-based auth)
2. **Artifact Push** - Pushing artifacts to OSDF storage
3. **Metadata Push/Pull** - Metadata synchronization
4. **Pull All Artifacts** - Downloading all artifacts for a pipeline
5. **Pull Single File** - Downloading individual file artifacts
6. **Pull Directory** - Downloading directory artifacts (`.dir` handling)
7. **Relative Path Handling** - Tests path duplication fix

### Security Regression Tests
1. **Path Traversal Validation** - Ensures malicious paths in `.dir` metadata are rejected
2. **Safe Parsing** - Verifies `eval()` has been replaced with `ast.literal_eval()`

## Prerequisites

### OSDF Credentials
You need either:

**Option 1: Token-based authentication**
```bash
export OSDF_TOKEN_PATH="~/.fdp/osdf_token"
Reach out to aalap.tripathy@hpe.com or martin.foltin@hpe.com to get required Tokens
```

**Option 2: Key-based authentication**
```bash
export OSDF_KEY_ID="your-key-id"
export OSDF_KEY_PATH="~/.fdp/osdf_private_key.pem"
export OSDF_KEY_ISSUER="https://your-issuer.org"
Reach out to aalap.tripathy@hpe.com or martin.foltin@hpe.com to get required Key_ID, KEY_PATH, KEY_ISSUER for this remote
```

### OSDF Configuration
```bash
export OSDF_REMOTE_REPO="https://fdp-origin.labs.hpe.com:8443/fdp-hpe/cmf_regression"
export OSDF_CACHE="https://osdf-director.osg-htc.org/"
```

## Running Tests

### Run all OSDF tests
```bash
cd /home/tripataa/cmf
pytest -vs test/client/test_osdf.py
```

### Run specific test
```bash
pytest -vs test/client/test_osdf.py::test_artifact_pull_directory
```

### Run with CMF server URL
```bash
pytest -vs --cmf_server_url=http://localhost:8080 test/client/test_osdf.py
```

## Test Data Requirements

The tests expect:
- A pipeline named "Test-env"
- Artifacts including:
  - `data.xml.gz` (file)
  - `artifacts/test_results` (directory)
  
You can generate this test data by running the example workflow first:
```bash
cd examples/example-get-started
./test_script.sh
```

## Key Regression Tests

### Path Duplication Fix (test_artifact_pull_with_relative_path)
**Issue Fixed**: When using relative MLMD paths like `./pull/mlmd`, `download_loc` was joined with `current_directory` twice, creating nested paths like `./pull/./pull/...`

**Test**: Verifies artifacts download to the correct location without path duplication.

### Directory Artifact Handling (test_artifact_pull_directory)
**Issue Fixed**: `.dir` artifacts (directories) require special handling to download all contained files.

**Test**: Ensures directories are downloaded completely with all their contents.

### Path Traversal Security (test_osdf_security_path_validation)
**Issue Fixed**: Malicious `.dir` metadata could include `../` or absolute paths to write outside the intended directory.

**Test**: Documents that path validation is in place (reject absolute paths, parent traversal, enforce containment).

### Code Execution Vulnerability (test_osdf_eval_replaced_with_literal_eval)
**Issue Fixed**: `eval()` was used to parse `.dir` metadata, allowing arbitrary code execution.

**Test**: Documents that `ast.literal_eval()` is now used for safe parsing.

## Continuous Integration

To add OSDF tests to CI:

1. Set up OSDF credentials as secrets
2. Add to test matrix:
```yaml
- name: Test OSDF Backend
  env:
    OSDF_TOKEN_PATH: ${{ secrets.OSDF_TOKEN_PATH }}
    OSDF_REMOTE_REPO: ${{ secrets.OSDF_REMOTE_REPO }}
    OSDF_CACHE: ${{ secrets.OSDF_CACHE }}
  run: pytest -vs test/client/test_osdf.py
```

## Troubleshooting

### Token Expired
```
ERROR: OSDF token has expired or is invalid
```
**Solution**: Refresh your token or regenerate it

### Connection Timeout
```
ERROR: Failed to download from cache/origin
```
**Solution**: Check OSDF service status and network connectivity

### Path Not Found
```
ERROR: Artifact not found in MLMD
```
**Solution**: Ensure test data exists and pipeline name matches
