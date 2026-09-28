###
# Copyright (2026) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
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

import requests
import pytest
from helpers import (
    assert_api_response,
    assert_success_response,
    response_data,
    response_summary,
)

pipeline_name = "Test-env"


@pytest.fixture(scope="function")
def server_url(cmf_server_url):
    # nginx routes all API calls under /api/v1/; strip trailing slash from base url
    return cmf_server_url.rstrip("/") + "/api/v1"


def _first_execution_uuid(server_url: str):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/executions", timeout=5)
    if response.status_code != 200 or not response.content:
        return None
    executions = response_data(response)
    if not isinstance(executions, list):
        return None
    for execution in executions:
        if not isinstance(execution, dict):
            continue
        execution_uuid = (
            execution.get("Execution_uuid")
            or execution.get("execution_uuid")
            or execution.get("uuid")
        )
        if execution_uuid:
            return str(execution_uuid).split(",")[0].strip()
    return None


def test_read_root(server_url):
    # The root health-check lives before the /api prefix
    base = server_url[: server_url.rfind("/api")]
    response = requests.get(f"{base}/")
    assert response.status_code == 200


def test_display_pipelines(server_url):
    response = requests.get(f"{server_url}/pipelines")
    assert response.status_code == 200
    # Body may be empty when no mlmd has been pushed to the server yet
    if response.content:
        assert_success_response(response, expected_data_type=list)


def test_display_artifact_types(server_url):
    response = requests.get(f"{server_url}/artifacts/types")
    # 404 is valid when no mlmd file has been pushed to the server yet
    assert response.status_code in (200, 404)
    if response.status_code == 200 and response.content:
        assert_success_response(response, expected_data_type=list)


def _get_stages(server_url: str) -> list:
    """Return the list of stages for pipeline_name, or an empty list if unavailable."""
    try:
        r = requests.get(f"{server_url}/pipelines/{pipeline_name}/stages", timeout=5)
        if r.status_code == 200 and r.content:
            data = response_data(r)
            if isinstance(data, dict):
                return data.get("stages", [])
    except Exception:
        pass
    return []


def test_display_executions(server_url):
    stages = _get_stages(server_url)
    if not stages:
        pytest.skip(f"No stages found for pipeline '{pipeline_name}' — skipping executions test")
    for stage in stages:
        response = requests.post(
            f"{server_url}/pipelines/{pipeline_name}/stages/{stage}/executions",
            json={"active_page": 1, "record_per_page": 5},
        )
        print(f"\n  stage={stage!r}  status={response.status_code}")
        assert response.status_code in (200, 404), (
            f"Unexpected response for stage {stage!r}: {response_summary(response)}"
        )
        if response.status_code == 200 and response.content:
            assert_success_response(response, expected_data_type=dict)


def test_display_artifacts(server_url):
    stages = _get_stages(server_url)
    if not stages:
        pytest.skip(f"No stages found for pipeline '{pipeline_name}' — skipping artifacts test")
    for stage in stages:
        response = requests.post(
            f"{server_url}/pipelines/{pipeline_name}/stages/{stage}/artifacts",
            json={"artifact_type": "Dataset", "active_page": 1, "record_per_page": 5},
        )
        print(f"\n  stage={stage!r}  status={response.status_code}")
        assert response.status_code in (200, 404), (
            f"Unexpected response for stage {stage!r}: {response_summary(response)}"
        )
        if response.status_code == 200 and response.content:
            assert_success_response(response, expected_data_type=dict)


def test_display_artifact_types_by_stage(server_url):
    stages = _get_stages(server_url)
    if not stages:
        pytest.skip(f"No stages found for pipeline '{pipeline_name}' — skipping artifact types test")
    for stage in stages:
        response = requests.post(
            f"{server_url}/pipelines/{pipeline_name}/stages/{stage}/artifacts/types"
        )
        print(f"\n  stage={stage!r}  status={response.status_code}")
        assert response.status_code in (200, 404), response_summary(response)
        if response.status_code == 200 and response.content:
            assert_success_response(response, expected_data_type=list)


def test_display_pipeline_artifacts(server_url):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/artifacts")
    assert_success_response(response, expected_data_type=list)


def test_display_pipeline_executions(server_url):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/executions")
    assert_success_response(response, expected_data_type=list)


def test_display_pipeline_execution_list(server_url):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/executions/list")
    assert_success_response(response, expected_data_type=list)


def test_display_artifact_lineage(server_url):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/artifacts/lineage")
    assert_success_response(response)


def test_display_artifact_execution_lineage(server_url):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/artifact-executions/lineage")
    assert_success_response(response)


def test_display_hierarchical_lineage(server_url):
    response = requests.get(f"{server_url}/pipelines/{pipeline_name}/hierarchical-lineage")
    assert_success_response(response)


def test_display_execution_lineage(server_url):
    execution_uuid = _first_execution_uuid(server_url)
    if not execution_uuid:
        pytest.skip(f"No execution uuid found for pipeline '{pipeline_name}'")
    response = requests.get(
        f"{server_url}/pipelines/{pipeline_name}/executions/{execution_uuid}/lineage"
    )
    assert_success_response(response)


def test_display_execution_python_env(server_url):
    execution_uuid = _first_execution_uuid(server_url)
    if not execution_uuid:
        pytest.skip(f"No execution uuid found for pipeline '{pipeline_name}'")
    response = requests.get(
        f"{server_url}/pipelines/{pipeline_name}/executions/{execution_uuid}/python-env"
    )
    assert response.status_code in (200, 404), response_summary(response)
    if response.status_code == 200:
        assert_success_response(response)
    elif response.content:
        assert_api_response(response, expected_statuses=("error",))
