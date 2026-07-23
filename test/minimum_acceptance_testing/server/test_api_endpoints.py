###
# Copyright (2023) Hewlett Packard Enterprise Development LP
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

pipeline_name = "Test-env"


@pytest.fixture(scope="function")
def server_url(cmf_server_url):
    # nginx routes all API calls under /api/; strip trailing slash from base url
    return cmf_server_url.rstrip("/") + "/api"


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
        assert isinstance(response.json(), list)


def test_display_artifact_types(server_url):
    response = requests.get(f"{server_url}/artifact_types")
    # 404 is valid when no mlmd file has been pushed to the server yet
    assert response.status_code in (200, 404)
    if response.status_code == 200 and response.content:
        assert isinstance(response.json(), list)


def _get_stages(server_url: str) -> list:
    """Return the list of stages for pipeline_name, or an empty list if unavailable."""
    try:
        r = requests.get(f"{server_url}/pipeline-stages/{pipeline_name}", timeout=5)
        if r.status_code == 200 and r.content:
            return r.json().get("stages", [])
    except Exception:
        pass
    return []


def test_display_executions(server_url):
    stages = _get_stages(server_url)
    if not stages:
        pytest.skip(f"No stages found for pipeline '{pipeline_name}' — skipping executions test")
    for stage in stages:
        params = {"stage_name": stage}
        response = requests.get(
            f"{server_url}/executions-by-stage/{pipeline_name}", params=params
        )
        print(f"\n  stage={stage!r}  status={response.status_code}")
        assert response.status_code in (200, 404), (
            f"Unexpected status {response.status_code} for stage {stage!r}"
        )
        if response.status_code == 200 and response.content:
            data = response.json()
            assert isinstance(data, dict)


def test_display_artifacts(server_url):
    stages = _get_stages(server_url)
    if not stages:
        pytest.skip(f"No stages found for pipeline '{pipeline_name}' — skipping artifacts test")
    for stage in stages:
        params = {"stage_name": stage, "artifact_type": "Dataset"}
        response = requests.get(
            f"{server_url}/artifacts-by-stage/{pipeline_name}", params=params
        )
        print(f"\n  stage={stage!r}  status={response.status_code}")
        assert response.status_code in (200, 404), (
            f"Unexpected status {response.status_code} for stage {stage!r}"
        )
        if response.status_code == 200 and response.content:
            data = response.json()
            assert isinstance(data, dict)

