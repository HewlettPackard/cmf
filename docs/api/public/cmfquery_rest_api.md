# CMFQuery REST API Reference

The CMFQuery REST APIs expose common `cmflib.cmfquery.CmfQuery` query operations through the CMF Server. Use these endpoints to retrieve pipeline, execution, artifact, and metrics metadata from the server database.

> For the Python API reference, see [CmfQuery](cmfquery.md). For CMF Server installation and setup instructions, see the [Installation & Setup](../../setup/index.md#install-cmf-server-with-gui) guide.

## API Reference

CMFQuery REST APIs are organized around [FastAPI](https://fastapi.tiangolo.com/). They accept JSON request bodies for `POST` endpoints and return JSON-encoded responses.

The application is configured with the `/api` root path and the CMFQuery routes use the `/v1` router prefix. In a standard CMF Server deployment, call these endpoints under `/api/v1`.

### Response Format

All endpoints return the standard `APIResponse` wrapper.

```json
{
  "status": "success",
  "code": 200,
  "data": {},
  "message": "Success",
  "errors": [],
  "meta": {
    "timestamp": "2026-09-08T00:00:00Z",
    "pagination": null
  }
}
```

Error responses use the same wrapper with `status` set to `error` and field-level details in `errors`.

## REST APIs

| Method | Route | Parameters | Description |
| --- | --- | --- | --- |
| `GET` | `/api/v1/pipelines/names` | None | Retrieves all pipeline names. |
| `GET` | `/api/v1/pipelines/{pipeline_name}/id` | Path: `pipeline_name` | Retrieves the numeric ID for a pipeline. |
| `GET` | `/api/v1/pipelines/{pipeline_name}/json` | Path: `pipeline_name`; optional query: `exec_uuid` | Exports metadata for one pipeline, optionally scoped to an execution UUID. |
| `GET` | `/api/v1/pipelines/sync/{last_sync_time}/json` | Path: `last_sync_time` | Exports pipeline metadata changed after the provided sync timestamp. |
| `GET` | `/api/v1/executions/pipeline/{pipeline_name}` | Path: `pipeline_name` | Retrieves executions for a pipeline. |
| `GET` | `/api/v1/executions/stages/name/{stage_name}` | Path: `stage_name` | Retrieves execution details for a pipeline stage name. |
| `GET` | `/api/v1/executions/stages/name/{stage_name}/list` | Path: `stage_name` | Retrieves execution objects for a pipeline stage name. |
| `GET` | `/api/v1/executions/stages/id/{stage_id}` | Path: `stage_id`; optional query: `execution_uuid` | Retrieves executions for a stage ID. |
| `POST` | `/api/v1/executions/batch-get` | Body: `exe_ids` | Retrieves execution details for a list of execution IDs. |
| `POST` | `/api/v1/executions/batch-summary` | Body: `exe_ids` | Retrieves an execution summary for a list of execution IDs. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/executions` | Path: `artifact_name` | Retrieves executions associated with an artifact name. |
| `GET` | `/api/v1/artifacts/id/{artifact_id}/executions` | Path: `artifact_id` | Retrieves executions associated with an artifact ID. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/parent-executions` | Path: `artifact_name` | Retrieves parent executions for an artifact. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/producer-execution` | Path: `artifact_name` | Retrieves the producer execution for an artifact. |
| `GET` | `/api/v1/executions/id/{execution_id}/artifacts` | Path: `execution_id` | Retrieves artifacts associated with one execution ID. |
| `GET` | `/api/v1/executions/id/{execution_id}/parents/ids` | Path: `execution_id`; optional query: `pipeline_id` | Retrieves one-hop parent execution IDs. |
| `POST` | `/api/v1/executions/parents/batch-get` | Body: `execution_id`, optional `pipeline_id` | Retrieves one-hop parent executions for execution IDs. |
| `POST` | `/api/v1/executions/ancestors/batch-get` | Body: `execution_id`, optional `pipeline_id` | Retrieves all parent executions and links for execution IDs. |
| `POST` | `/api/v1/executions/artifacts/batch-get` | Body: `exe_ids` | Retrieves artifacts for a list of execution IDs. |
| `GET` | `/api/v1/artifacts` | None | Retrieves all artifact names. |
| `GET` | `/api/v1/artifacts/{pipeline_name}` | Path: `pipeline_name` | Retrieves artifacts associated with a pipeline. |
| `POST` | `/api/v1/artifacts/batch-get` | Body: `artifact_ids` | Retrieves artifacts for a list of artifact IDs. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/dataframe` | Path: `artifact_name` | Retrieves an artifact dataframe by artifact name. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}` | Path: `artifact_name` | Retrieves artifact metadata by artifact name. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/children` | Path: `artifact_name`; optional query: `pipeline_id` | Retrieves one-hop child artifacts. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/descendants` | Path: `artifact_name` | Retrieves all downstream child artifacts. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/parents` | Path: `artifact_name` | Retrieves one-hop parent artifacts by artifact name. |
| `GET` | `/api/v1/artifacts/id/{artifact_id}/parents` | Path: `artifact_id` | Retrieves one-hop parent artifacts by artifact ID. |
| `GET` | `/api/v1/artifacts/name/{artifact_name}/ancestors` | Path: `artifact_name` | Retrieves all upstream parent artifacts by artifact name. |
| `GET` | `/api/v1/artifacts/metrics/{metrics_name}` | Path: `metrics_name` | Retrieves metrics metadata by metrics name. |

### Request Bodies

Use `exe_ids` when the endpoint accepts `ExecutionIdsRequest`.

```json
{
  "exe_ids": [1, 2, 3]
}
```

Use `execution_id` when the endpoint accepts `ExecutionIdsWithPipelineRequest`.

```json
{
  "execution_id": [1, 2, 3],
  "pipeline_id": 10
}
```

### Examples

```bash
curl http://localhost:80/api/v1/executions/pipeline/MyPipeline
curl http://localhost:80/api/v1/executions/stages/name/train
curl -X POST http://localhost:80/api/v1/executions/batch-get \
  -H "Content-Type: application/json" \
  -d '{"exe_ids":[1,2,3]}'
curl http://localhost:80/api/v1/pipelines/names
curl "http://localhost:80/api/v1/pipelines/MyPipeline/json?exec_uuid=run-001"
curl http://localhost:80/api/v1/artifacts/MyPipeline
curl http://localhost:80/api/v1/artifacts/name/model.pkl/executions
curl http://localhost:80/api/v1/artifacts/id/11/executions
curl http://localhost:80/api/v1/artifacts/name/model.pkl/parent-executions
curl "http://localhost:80/api/v1/artifacts/name/model.pkl/children?pipeline_id=10"
curl -X POST http://localhost:80/api/v1/artifacts/batch-get \
  -H "Content-Type: application/json" \
  -d '{"artifact_ids":[11,12,13]}'
curl http://localhost:80/api/v1/artifacts/metrics/accuracy
```

## HTTP Response Status Codes

| Code  | Title                   | Description                                                                 |
| ----- | ----------------------- | --------------------------------------------------------------------------- |
| `200` | `OK`                    | Request completed successfully.                                             |
| `404` | `Not Found`            | Requested pipeline, stage, execution, artifact, metrics, or data not found. |
| `422` | `Unprocessable Entity`  | Request validation failed, such as a missing or invalid request body field.  |
| `500` | `Internal Server Error` | Server error occurred while processing the query.                           |
