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
from helpers import (
    assert_cmfquery_response,
    path_param,
)

# Test configuration for CMF query API endpoints
pipeline_name = "Test-env"
artifact_name = "data.xml.gz"
artifact_id = 1
metrics_name = "metrics"
stage_name = "parse"
stage_id = 1
execution_id = 1


def _path(value, safe=""):
    return path_param(value, safe=safe)


@pytest.fixture(scope="function")
def server_url(cmf_server_url):
    # nginx routes all API calls under /api/v1/; strip trailing slash from base url
    return cmf_server_url.rstrip("/") + "/api/v1"


def _assert_response(response):
    print(response.text)
    assert_cmfquery_response(response)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/pipelines/names",
        f"/pipelines/{_path(pipeline_name)}/id",
        f"/pipelines/{_path(pipeline_name)}/json",
        "/pipelines/sync/0/json",
        "/artifacts",
        f"/artifacts/{_path(pipeline_name)}",
        f"/artifacts/name/{_path(artifact_name, safe='/')}/dataframe",
        f"/artifacts/name/{_path(artifact_name, safe='/')}",
        f"/artifacts/metrics/{_path(metrics_name, safe='/')}",
        f"/artifacts/id/{artifact_id}/parents",
        f"/artifacts/id/{artifact_id}/executions",
        f"/executions/stages/name/{_path(stage_name, safe='/')}/list",
        f"/executions/stages/name/{_path(stage_name, safe='/')}",
        f"/executions/pipeline/{_path(pipeline_name)}",
        f"/executions/id/{execution_id}/parents/ids",
        f"/executions/stages/id/{stage_id}",
        f"/executions/id/{execution_id}/artifacts",
    ],
)
def test_cmfquery_get_endpoints(server_url, endpoint):
    # Test the GET request for the given CMF query endpoint
    response = requests.get(f"{server_url}{endpoint}")
    _assert_response(response)


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
    response = requests.get(
        f"{server_url}{endpoint.format(artifact_name=_path(artifact_name, safe='/'))}"
    )
    _assert_response(response)


def test_cmfquery_artifact_batch_get(server_url):
    # Test the POST request for batch retrieval of artifacts by their IDs
    response = requests.post(
        f"{server_url}/artifacts/batch-get",
        json={"artifact_ids": [artifact_id]},
    )
    _assert_response(response)


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("/executions/batch-get", "exe_ids"),
        ("/executions/batch-summary", "exe_ids"),
        ("/executions/artifacts/batch-get", "exe_ids"),
    ],
)
def test_cmfquery_execution_id_batch_endpoints(server_url, endpoint, payload):
    # Test the POST request for batch retrieval of executions by their IDs
    response = requests.post(
        f"{server_url}{endpoint}",
        json={payload: [execution_id]},
    )
    _assert_response(response)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/executions/parents/batch-get",
        "/executions/ancestors/batch-get",
    ],
)
def test_cmfquery_parent_execution_batch_endpoints(server_url, endpoint):
    # Test the POST request for batch retrieval of parent executions
    payload = {"execution_id": [execution_id], "pipeline_id": 1}
    response = requests.post(f"{server_url}{endpoint}", json=payload)
    _assert_response(response)
