# CMF Server API Reference

**CMF Server** is a key interface for users to explore and track their ML training runs by storing metadata files on the CMF Server. Users can retrieve the saved metadata files and view their content using the UI provided by the CMF Server.

> For CMF Server installation and setup instructions, see the [Installation & Setup](../../setup/index.md#install-cmf-server-with-gui) guide.

## API Reference

CMF Server APIs are implemented with [FastAPI](https://fastapi.tiangolo.com/). The server registers routes under `/v1`; when accessed through the default CMF server/nginx setup, the public URL prefix is usually `/api/v1`.

Use the following parameter convention when adding or calling APIs:

- Required identifiers belong in the path, for example `{pipeline_name}`, `{execution_uuid}`, `{model_id}`, `{server_id}`, `{schedule_id}`, and `{file_name}`.
- Optional filters, search values, sorting, paging, or flags belong in query parameters, for example `server_id`, `skip_logging`, and `list_of_files`.
- Request bodies are used for structured create, sync, push, pull, or paginated query payloads.

## Response Format

Successful endpoints return a common response envelope:

```json
{
	"status": "success",
	"code": 200,
	"data": {},
	"message": "Pipelines retrieved successfully",
	"errors": [],
	"meta": {
		"timestamp": "2026-01-04T15:00:00Z",
		"pagination": null
	}
}
```

Error responses use the same envelope with `status: "error"` and field-level details in `errors`.

> **Exception:** `POST /v1/mlmd/pull` does not use this envelope. It returns the raw MLMD JSON payload directly as its response body.

### REST APIs

| Method | Route | Parameters | Description |
| --- | --- | --- | --- |
| `GET` | `/v1/pipelines` | None | Discovers all pipelines present in the MLMD store. No parameters required. |
| `GET` | `/v1/pipelines/{pipeline_name}/stages` | Path: `pipeline_name` | Retrieves unique stages for a pipeline. |
| `GET` | `/v1/pipelines/{pipeline_name}/artifacts` | Path: `pipeline_name` | Discovers all artifacts for a pipeline. `pipeline_name` is a required path parameter. |
| `POST` | `/v1/pipelines/{pipeline_name}/stages/{stage}/artifacts/types` | Path: `pipeline_name`, `stage` | Retrieves artifact types available in a pipeline stage. |
| `POST` | `/v1/pipelines/{pipeline_name}/stages/{stage}/artifacts` | Path: `pipeline_name`, `stage`; body: artifact stage query options | Retrieves artifacts filtered by pipeline stage, artifact type, search, sort, and pagination options. |
| `GET` | `/v1/pipelines/{pipeline_name}/executions` | Path: `pipeline_name` | Discovers all executions in a pipeline. `pipeline_name` is a required path parameter. |
| `GET` | `/v1/pipelines/{pipeline_name}/executions/list` | Path: `pipeline_name` | Retrieves a short list of executions for a pipeline. |
| `POST` | `/v1/pipelines/{pipeline_name}/stages/{stage}/executions` | Path: `pipeline_name`, `stage`; body: execution stage query options | Retrieves executions filtered by pipeline stage, search, sort, and pagination options. |
| `GET` | `/v1/pipelines/{pipeline_name}/executions/{execution_uuid}/python-env` | Path: `pipeline_name`, `execution_uuid` | Retrieves the Python environment file associated with an execution. Uses `pipeline_name` and `execution_uuid` so MCP does not need the raw environment file name. |
| `GET` | `/v1/pipelines/{pipeline_name}/executions/{uuid}/lineage` | Path: `pipeline_name`, `uuid` | Retrieves execution lineage for a selected execution UUID. |
| `GET` | `/v1/pipelines/{pipeline_name}/artifacts/lineage` | Path: `pipeline_name` | Retrieves artifact lineage for a pipeline. |
| `GET` | `/v1/pipelines/{pipeline_name}/artifact-executions/lineage` | Path: `pipeline_name` | Retrieves combined artifact and execution lineage for a pipeline. |
| `GET` | `/v1/artifacts/types` | None | Retrieves available artifact types. |
| `GET` | `/v1/artifacts/models/{model_id}/card` | Path: `model_id` | Retrieves model card data for a Model artifact. `model_id` is a required path parameter; MCP should first discover Model artifacts and use the selected artifact ID. |
| `POST` | `/v1/mlmd/push` | Body: `pipeline_name`, `json_payload`, optional `exec_uuid` | Pushes MLMD metadata to the CMF Server. |
| `POST` | `/v1/mlmd/pull` | Body: optional `pipeline_name`, optional `exec_uuid`, optional `last_sync_time` | Pulls MLMD metadata from the CMF Server. Returns the raw MLMD JSON payload directly, not the standard response envelope. |
| `POST` | `/v1/python-env` | Multipart file: `file` | Uploads a Python environment file to the CMF Server. |
| `GET` | `/v1/python-env/{file_name}` | Path: `file_name` | Retrieves a Python environment file by file name. |
| `GET` | `/v1/python-env/download` | Optional query: `list_of_files` | Downloads Python environment files as a ZIP archive. |
| `GET` | `/v1/model-card` | Query: `modelId` | Retrieves model card data for the UI by model artifact ID. |
| `POST` | `/v1/label` | Multipart file: `file` | Uploads a label file to the CMF Server. |
| `GET` | `/v1/label-data` | Query: `file_name` | Retrieves label file content by file name. |
| `POST` | `/v1/tensorboard` | Query: `pipeline_name`; multipart file: `file` | Uploads TensorBoard logs for a pipeline. |
| `POST` | `/v1/acknowledge` | Body: `server_name`, `server_url` | Acknowledges a peer server during registration or liveness checks. |
| `POST` | `/v1/servers/register` | Body: `server_name`, `server_url` | Registers a peer CMF Server. |
| `POST` | `/v1/servers/sync` | Body: `server_name`, `server_url`; optional query: `skip_logging` | Synchronizes metadata from a registered server. |
| `GET` | `/v1/servers` | None | Lists registered servers. |
| `GET` | `/v1/servers/{server_id}/completed-logs` | Path: `server_id` | Retrieves completed sync logs for a registered server. |
| `POST` | `/v1/schedules` | Body: schedule creation details | Creates a sync schedule. |
| `GET` | `/v1/schedules` | Optional query: `server_id` | Retrieves active schedules, optionally filtered by server. |
| `GET` | `/v1/schedules/{schedule_id}/logs` | Path: `schedule_id` | Retrieves run history logs for a schedule. |
| `DELETE` | `/v1/schedules/{schedule_id}` | Path: `schedule_id` | Deactivates a sync schedule. |

### HTTP Response Status Codes

| Code | Title | Description |
| --- | --- | --- |
| `200` | `OK` | Request completed successfully. |
| `201` | `Created` | Resource or uploaded file was created successfully. |
| `400` | `Bad Request` | Request parameters or body are invalid, such as using a non-Model artifact ID for a model card. |
| `404` | `Not Found` | Requested resource was not found, such as a pipeline, execution, artifact, file, server, or schedule. |
| `406` | `Not Acceptable` | `POST /v1/mlmd/pull` could not find the requested pipeline. |
| `422` | `Unprocessable Entity` | Request validation failed or a metadata schema version update is required. |
| `500` | `Internal Server Error` | Server error occurred, such as file read failure, sync failure, or an unexpected backend error. |