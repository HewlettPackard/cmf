# CMFQuery Curl Commands

Use this file to test the CMFQuery REST APIs directly from a terminal.

The UI page you open in the browser may be:

```bash
DISPLAY_LINEAGE_URL="http://10.93.232.89/display_lineage"
```

The REST API base URL is different. All curl examples below use this direct API URL:

```bash
http://10.93.232.89/api/v1
```

If `jq` is installed, keep `| jq` at the end of commands for formatted JSON. If `jq` is not installed, remove `| jq`.

Before running ID-based APIs, update these values with IDs/names from your MLMD data:

```bash
PIPELINE_NAME="Test-env1"
PIPELINE_ID=1
ARTIFACT_ID=1
ARTIFACT_NAME="example-artifact-name"
METRICS_NAME="example-metrics-name"
EXECUTION_ID=1
EXECUTION_UUID="example-execution-uuid"
STAGE_NAME="example-stage-name"
STAGE_ID=1
LAST_SYNC_TIME=0
```

## Quick Smoke Tests

List all pipelines using the UI pipeline API. This is useful to confirm the server and MLMD state are reachable before testing CMFQuery APIs.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines" | jq
```

Get a pipeline ID using CMFQuery.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines/Test-env/id" | jq
```

Dump a pipeline as JSON using CMFQuery.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines/Test-env/json" | jq
```

## Pipeline CMFQuery APIs

Get a pipeline ID.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines/Test-env/id" | jq
```

Dump a full pipeline to JSON.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines/Test-env/json" | jq
```

Dump one execution UUID from a pipeline to JSON.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines/Test-env/json?exec_uuid=$EXECUTION_UUID" | jq
```

Extract pipelines changed since a sync time.

```bash
curl -sS "http://10.93.232.89/api/v1/pipelines/sync/$LAST_SYNC_TIME/json" | jq
```

## Artifact CMFQuery APIs

Get all artifact names.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts" | jq
```

Get artifacts by artifact IDs.

```bash
curl -sS -X POST "http://10.93.232.89/api/v1/artifacts/by-ids" \
  -H "Content-Type: application/json" \
  -d "{\"artifact_ids\":[$ARTIFACT_ID]}" | jq
```

Get all artifacts for execution IDs.

```bash
curl -sS -X POST "http://10.93.232.89/api/v1/executions/artifacts" \
  -H "Content-Type: application/json" \
  -d "{\"exe_ids\":[5]}" | jq
```

Get artifact dataframe by artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/dataframe/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get artifact by artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/name/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get one-hop child artifacts by artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/children/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get one-hop child artifacts by artifact name and pipeline ID.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/children/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81?pipeline_id=1" | jq
```

Get all child artifacts by artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/children/all/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get one-hop parent artifacts by artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/parents/name/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get one-hop parent artifacts by artifact ID.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/parents/id/$ARTIFACT_ID" | jq
```

Get all parent artifacts by artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/artifacts/parents/all/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get metrics by metrics artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/metrics/$METRICS_NAME" | jq
```

## Execution CMFQuery APIs

Get executions in a stage as dataframe-style records.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/stages/name/$STAGE_NAME" | jq
```

List executions in a stage as MLMD execution objects converted to dictionaries.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/stages/list/$STAGE_NAME" | jq
```

Get executions by execution IDs.

```bash
curl -sS -X POST "http://10.93.232.89/api/v1/executions/by-ids" \
  -H "Content-Type: application/json" \
  -d "{\"exe_ids\":[5]}" | jq
```

Get all executions for an artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/artifacts/name/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get all executions for an artifact ID.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/artifacts/id/$ARTIFACT_ID" | jq
```

Get one-hop parent executions for execution IDs.

```bash
curl -sS -X POST "http://10.93.232.89/api/v1/executions/one-hop/parents" \
  -H "Content-Type: application/json" \
  -d "{\"execution_id\":[5],\"pipeline_id\":1}" | jq
```

Get one-hop parent execution IDs for one execution ID.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/5/one-hop/parent/executions/ids" | jq
```

Get one-hop parent execution IDs for one execution ID and pipeline ID.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/5/one-hop/parent/executions/ids?pipeline_id=1" | jq
```

Get all parent executions for execution IDs.

```bash
curl -sS -X POST "http://10.93.232.89/api/v1/executions/parents/all" \
  -H "Content-Type: application/json" \
  -d "{\"execution_id\":[5],\"pipeline_id\":1}" | jq
```

Get all parent executions for an artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/artifacts/parents/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get execution summary by execution IDs.

```bash
curl -sS -X POST "http://10.93.232.89/api/v1/executions/summary" \
  -H "Content-Type: application/json" \
  -d "{\"exe_ids\":[5]}" | jq
```

Get executions by stage ID.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/stages/id/$STAGE_ID" | jq
```

Get executions by stage ID and execution UUID.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/stages/id/$STAGE_ID?execution_uuid=$EXECUTION_UUID" | jq
```

Find the producer execution for an artifact name.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/artifacts/producer/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81" | jq
```

Get all artifacts for one execution ID.

```bash
curl -sS "http://10.93.232.89/api/v1/executions/5/artifacts" | jq
```

## Notes For Names With Slashes Or Spaces

Some artifact or stage names may contain `/`, spaces, or other special characters. If a command fails because of the name, URL-encode the value before calling curl.

Example:

```bash
ARTIFACT_NAME_ENCODED="$(python3 -c 'import urllib.parse, os; print(urllib.parse.quote(os.environ["ARTIFACT_NAME"], safe=""))')"
curl -sS "http://10.93.232.89/api/v1/artifacts/name/artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81_ENCODED" | jq
```

For path parameters declared with `{name:path}`, slash-containing names can also work directly when nginx and the client preserve the path correctly. URL encoding is still safer for spaces and special characters.

## Expected Response Shape

Successful CMFQuery APIs return a wrapped response similar to:

```json
{
  "success": true,
  "message": "...",
  "data": {}
}
```

Handled errors return the same wrapper style with `success` false and error details, for example when a pipeline, artifact, execution, or stage is not found.
