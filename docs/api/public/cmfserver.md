## API Reference - NEEDS TO BE UPDATED
cmf-server APIs are organized around [FastAPI](https://fastapi.tiangolo.com/).
They accept and return JSON-encoded request bodies and responses and return standard HTTP response codes.

### List of APIs

| Method | URL                                                        | Description                                                                                        |
| ------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `POST` | `/mlmd_push`                                               | Pushes JSON-encoded data to the cmf-server.                                                        |
| `GET`  | `/mlmd_pull/{pipeline_name}`                               | Retrieves an MLMD file from the cmf-server.                                                        |
| `GET`  | `/executions/{pipeline_name}`                              | Retrieves all executions from the cmf-server.                                                      |
| `GET`  | `/list-of-executions/{pipeline_name}`                      | Retrieves a list of execution types.                                                               |
| `GET`  | `/execution-lineage/tangled-tree/{uuid}/{pipeline_name}`   | Retrieves a dictionary of nodes and links for a given execution type.                              |
| `GET`  | `/artifacts/{pipeline_name}/{type}`                        | Retrieves all artifacts of the specified type from the cmf-server.                                 |
| `GET`  | `/artifact-lineage/tangled-tree/{pipeline_name}`           | Retrieves a nested list of dictionaries with `id` and `parents` keys for artifacts.                |
| `GET`  | `/artifact_types`                                          | Retrieves a list of artifact types.                                                                |
| `GET`  | `/pipelines`                                               | Retrieves all pipelines present in the MLMD file.                                                  |
| `POST` | `/tensorboard`                                             | Uploads TensorBoard logs to the cmf-server.                                                        |
| `GET`  | `/model-card`                                              | Retrieves model data, input/output artifacts, and executions for a model.                          |
| `GET`  | `/artifact-execution-lineage/tangled-tree/{pipeline_name}` | Retrieves a nested list of dictionaries with `id` and `parents` keys for artifacts and executions. |
| `POST` | `/python-env`                                              | Pushes Python environment data to the cmf-server.                                                  |
| `GET`  | `/python-env`                                              | Retrieves environment data from the `/cmf-server/data/env` folder.                                 |

### HTTP Response Status codes

| Code  | Title                     | Description                                                  |
|-------| ------------------------- |--------------------------------------------------------------|
| `200` | `OK`                      | mlmd is successfully pushed (e.g. when using `GET`, `POST`). |
| `400` | `Bad request`             | When the cmf-server is not available.                        |
| `500` | `Internal server error`   | When an internal error has happened                          |
