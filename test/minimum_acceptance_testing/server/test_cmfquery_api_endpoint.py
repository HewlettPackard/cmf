###
# Copyright (2026) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

import pytest
import requests
from _helpers import (
    assert_cmfquery_response,
    path_param,
    response_data,
)

pipeline_name = "Test-env"
missing_artifact_name = "missing-artifact"
missing_metrics_name = "missing-metrics"


def _path(value, safe=""):
    return path_param(value, safe=safe)


@pytest.fixture(scope="function")
def server_url(cmf_server_url):
    # nginx routes all API calls under /api/v1/; strip trailing slash from base url
    return cmf_server_url.rstrip("/") + "/api/v1"


def _get_pipeline_name(server_url):
    response = requests.get(f"{server_url}/pipelines/names", timeout=5)
    assert_cmfquery_response(response)
    data = response_data(response)
    if isinstance(data, dict) and data.get("pipelines"):
        return data["pipelines"][0]
    return pipeline_name


def _get_pipeline_id(server_url, pipeline):
    response = requests.get(f"{server_url}/pipelines/{_path(pipeline)}/id", timeout=5)
    assert_cmfquery_response(response)
    data = response_data(response)
    if isinstance(data, dict):
        return data.get("pipeline_id")
    return None


def _get_stage_name(server_url, pipeline):
    response = requests.get(f"{server_url}/pipelines/{_path(pipeline)}/stages", timeout=5)
    if response.status_code == 200 and response.content:
        data = response_data(response)
        if isinstance(data, dict) and data.get("stages"):
            return data["stages"][0]
    return pipeline


def _first_value(records, *keys):
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                return value
    return None


def _get_artifact_info(server_url, pipeline):
    response = requests.get(f"{server_url}/artifacts/{_path(pipeline)}", timeout=5)
    assert_cmfquery_response(response)
    data = response_data(response)
    artifacts = data.get("artifacts", []) if isinstance(data, dict) else []
    artifact_name = _first_value(artifacts, "name", "artifact_name", "uri")
    artifact_id = _first_value(artifacts, "id", "artifact_id", "Artifact_ID")
    metrics_name = None
    for artifact in artifacts:
        if isinstance(artifact, dict) and artifact.get("type") == "Metrics":
            metrics_name = artifact.get("name") or artifact.get("artifact_name")
            break
    return {
        "name": artifact_name or missing_artifact_name,
        "id": artifact_id or 1,
        "metrics_name": metrics_name or missing_metrics_name,
    }


def _get_execution_info(server_url, pipeline):
    response = requests.get(f"{server_url}/executions/pipeline/{_path(pipeline)}", timeout=5)
    assert_cmfquery_response(response)
    data = response_data(response)
    executions = data.get("executions", []) if isinstance(data, dict) else []
    execution_id = _first_value(executions, "id", "execution_id", "Execution_ID")
    stage_id = _first_value(executions, "Context_ID", "context_id", "stage_id", "Stage_ID")
    execution_uuid = _first_value(executions, "Execution_uuid", "execution_uuid", "uuid")
    if execution_uuid:
        execution_uuid = str(execution_uuid).split(",")[0].strip()
    return {
        "id": execution_id or 1,
        "stage_id": stage_id or 1,
        "uuid": execution_uuid,
    }


def test_cmfquery_pipeline_endpoints(server_url):
    pipeline = _get_pipeline_name(server_url)
    endpoints = [
        (f"/pipelines/{_path(pipeline)}/id", ("pipeline_name", "pipeline_id")),
        (f"/pipelines/{_path(pipeline)}/json", None),
        ("/pipelines/sync/0/json", None),
    ]
    for endpoint, expected_keys in endpoints:
        response = requests.get(f"{server_url}{endpoint}")
        assert_cmfquery_response(response, expected_data_keys=expected_keys)


def test_cmfquery_list_pipeline_names(server_url):
    response = requests.get(f"{server_url}/pipelines/names")
    assert_cmfquery_response(response, expected_data_keys=("pipelines", "total_pipelines"))


def test_cmfquery_artifact_collection_endpoints(server_url):
    pipeline = _get_pipeline_name(server_url)
    artifact = _get_artifact_info(server_url, pipeline)
    endpoints = [
        ("/artifacts", ("artifacts", "total_artifacts")),
        (f"/artifacts/{_path(pipeline)}", ("pipeline_name", "artifacts", "total_artifacts")),
        (f"/artifacts/name/{_path(artifact['name'], safe='/')}/dataframe", ("artifact_name", "artifacts", "total_artifacts")),
        (f"/artifacts/name/{_path(artifact['name'], safe='/')}", ("artifact_name", "artifacts", "total_artifacts")),
        (f"/artifacts/metrics/{_path(artifact['metrics_name'], safe='/')}", ("metrics_name", "metrics", "total_metrics")),
    ]
    for endpoint, expected_keys in endpoints:
        response = requests.get(f"{server_url}{endpoint}")
        assert_cmfquery_response(response, expected_data_keys=expected_keys)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/artifacts/name/{artifact_name}/children",
        "/artifacts/name/{artifact_name}/descendants",
        "/artifacts/name/{artifact_name}/parents",
        "/artifacts/name/{artifact_name}/ancestors",
        "/artifacts/name/{artifact_name}/executions",
        "/artifacts/name/{artifact_name}/parent-executions",
        "/artifacts/name/{artifact_name}/producer-execution",
    ],
)
def test_cmfquery_artifact_name_relationship_endpoints(server_url, endpoint):
    pipeline = _get_pipeline_name(server_url)
    artifact = _get_artifact_info(server_url, pipeline)
    response = requests.get(
        f"{server_url}{endpoint.format(artifact_name=_path(artifact['name'], safe='/'))}"
    )
    assert_cmfquery_response(response)


def test_cmfquery_artifact_id_relationship_endpoints(server_url):
    pipeline = _get_pipeline_name(server_url)
    artifact = _get_artifact_info(server_url, pipeline)
    endpoints = [
        f"/artifacts/id/{artifact['id']}/parents",
        f"/artifacts/id/{artifact['id']}/executions",
    ]
    for endpoint in endpoints:
        response = requests.get(f"{server_url}{endpoint}")
        assert_cmfquery_response(response)


def test_cmfquery_artifact_batch_get(server_url):
    pipeline = _get_pipeline_name(server_url)
    artifact = _get_artifact_info(server_url, pipeline)
    response = requests.post(
        f"{server_url}/artifacts/batch-get",
        json={"artifact_ids": [artifact["id"]]},
    )
    assert_cmfquery_response(response, expected_data_keys=("artifact_ids", "artifacts", "total_artifacts"))


def test_cmfquery_execution_stage_endpoints(server_url):
    pipeline = _get_pipeline_name(server_url)
    stage_name = _get_stage_name(server_url, pipeline)
    endpoints = [
        (f"/executions/stages/name/{_path(stage_name, safe='/')}/list", ("stage_name", "executions", "total_executions")),
        (f"/executions/stages/name/{_path(stage_name, safe='/')}", ("stage_name", "executions", "total_executions")),
    ]
    for endpoint, expected_keys in endpoints:
        response = requests.get(f"{server_url}{endpoint}")
        assert_cmfquery_response(response, expected_data_keys=expected_keys)


def test_cmfquery_execution_collection_endpoints(server_url):
    pipeline = _get_pipeline_name(server_url)
    execution = _get_execution_info(server_url, pipeline)
    endpoints = [
        (f"/executions/pipeline/{_path(pipeline)}", ("pipeline_name", "executions", "total_executions")),
        (f"/executions/id/{execution['id']}/parents/ids", ("execution_id", "parent_execution_ids", "total_parent_execution_ids")),
        (f"/executions/stages/id/{execution['stage_id']}", ("stage_id", "executions", "total_executions")),
        (f"/executions/id/{execution['id']}/artifacts", ("execution_id", "artifacts", "total_artifacts")),
    ]
    if execution["uuid"]:
        endpoints.append(
            (f"/executions/stages/id/{execution['stage_id']}?execution_uuid={execution['uuid']}", ("stage_id", "execution_uuid", "executions", "total_executions"))
        )
    for endpoint, expected_keys in endpoints:
        response = requests.get(f"{server_url}{endpoint}")
        assert_cmfquery_response(response, expected_data_keys=expected_keys)


@pytest.mark.parametrize(
    "endpoint,payload,expected_keys",
    [
        ("/executions/batch-get", "exe_ids", ("exe_ids", "executions", "total_executions")),
        ("/executions/batch-summary", "exe_ids", ("exe_ids", "executions", "total_executions")),
        ("/executions/artifacts/batch-get", "exe_ids", ("exe_ids", "artifacts", "total_artifacts")),
    ],
)
def test_cmfquery_execution_id_batch_endpoints(server_url, endpoint, payload, expected_keys):
    pipeline = _get_pipeline_name(server_url)
    execution = _get_execution_info(server_url, pipeline)
    response = requests.post(
        f"{server_url}{endpoint}",
        json={payload: [execution["id"]]},
    )
    assert_cmfquery_response(response, expected_data_keys=expected_keys)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/executions/parents/batch-get",
        "/executions/ancestors/batch-get",
    ],
)
def test_cmfquery_parent_execution_batch_endpoints(server_url, endpoint):
    pipeline = _get_pipeline_name(server_url)
    pipeline_id = _get_pipeline_id(server_url, pipeline)
    execution = _get_execution_info(server_url, pipeline)
    payload = {"execution_id": [execution["id"]]}
    if pipeline_id is not None:
        payload["pipeline_id"] = pipeline_id
    response = requests.post(f"{server_url}{endpoint}", json=payload)
    assert_cmfquery_response(response)
