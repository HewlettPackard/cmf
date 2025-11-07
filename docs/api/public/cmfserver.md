# CMF Server API Reference

**CMF Server** is a key interface for users to explore and track their ML training runs by storing metadata files on the CMF Server. Users can retrieve the saved metadata files and view their content using the UI provided by the CMF Server.

> For CMF Server installation and setup instructions, see the [Installation & Setup](../../setup/index.md#install-cmf-server-with-gui) guide.

## API Reference

CMF Server APIs are organized around [FastAPI](https://fastapi.tiangolo.com/).
They accept and return JSON-encoded request bodies and responses and return standard HTTP response codes.

### List of APIs

| Method | URL                                                        | Description                                                                                        |
| ------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `POST` | `/mlmd_push`                                               | Pushes JSON-encoded data to the CMF Server.                                                        |
| `GET`  | `/mlmd_pull/{pipeline_name}`                               | Retrieves an MLMD file from the CMF Server.                                                        |
| `GET`  | `/executions/{pipeline_name}`                              | Retrieves all executions from the CMF Server.                                                      |
| `GET`  | `/list-of-executions/{pipeline_name}`                      | Retrieves a list of execution types.                                                               |
| `GET`  | `/execution-lineage/tangled-tree/{uuid}/{pipeline_name}`   | Retrieves a dictionary of nodes and links for a given execution type.                              |
| `GET`  | `/artifacts/{pipeline_name}/{type}`                        | Retrieves all artifacts of the specified type from the CMF Server.                                 |
| `GET`  | `/artifact-lineage/tangled-tree/{pipeline_name}`           | Retrieves a nested list of dictionaries with `id` and `parents` keys for artifacts.                |
| `GET`  | `/artifact_types`                                          | Retrieves a list of artifact types.                                                                |
| `GET`  | `/pipelines`                                               | Retrieves all pipelines present in the MLMD file.                                                  |
| `POST` | `/tensorboard`                                             | Uploads TensorBoard logs to the CMF Server.                                                        |
| `GET`  | `/model-card`                                              | Retrieves model data, input/output artifacts, and executions for a model.                          |
| `GET`  | `/artifact-execution-lineage/tangled-tree/{pipeline_name}` | Retrieves a nested list of dictionaries with `id` and `parents` keys for artifacts and executions. |
| `POST` | `/python-env`                                              | Pushes Python environment data to the CMF Server.                                                  |
| `GET`  | `/python-env`                                              | Retrieves environment data from the `/cmf_server/data/env` folder.                                 |

### HTTP Response Status Codes

| Code  | Title                     | Description                                                                                      |
|-------|---------------------------|--------------------------------------------------------------------------------------------------|
| `200` | `OK`                      | MLMD is successfully pushed (e.g., when using `GET`, `POST`).                                        |
| `400` | `Bad Request`             | When the CMF Server is not available. |
| `404` | `Not Found`               | Requested resource not found (e.g., pipeline, database, file, or registered server).            |
| `406` | `Not Acceptable`          | Pipeline not found in the database.                                                              |
| `422` | `Unprocessable Entity`    | Version update required. The metadata schema version is incompatible.                            |
| `500` | `Internal Server Error`   | Server error occurred (e.g., target server unreachable, file read error, sync failure).         |
