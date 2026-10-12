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

from urllib.parse import quote

import pytest

# CMF failure message prefixes (from cmf_exception_handling.py CmfFailure subclasses).
_CMF_FAILURE_PREFIXES = (
    "ERROR:",
    "Error:",
    "'cmf' is not configured",
    "cmf-server error:",
    "INFO: No changes made",           # NoChangesMadeInfo is a CmfFailure
    "INFO: Number of files downloaded", # BatchDownloadFailure is a CmfFailure
)

# Substrings that also indicate failure (for CmfFailure messages without a standard prefix).
_CMF_FAILURE_SUBSTRINGS = (
    "is not downloaded.",   # ObjectDownloadFailure: "Object {name} is not downloaded."
    "Files failed to download",  # belt-and-suspenders for BatchDownloadFailure
)

_CMF_INIT_STATUS = {}


def path_param(value, safe=""):
    """URL-quote a dynamic API path parameter."""
    return quote(str(value), safe=safe)


def json_payload(response):
    """Return the JSON response body, failing with response text when it is not JSON."""
    try:
        return response.json()
    except ValueError:
        pytest.fail(f"Expected JSON response, got: {response.text}")


def response_data(response):
    """Return data from the standard API response envelope, or raw JSON for legacy responses."""
    data = json_payload(response)
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


def response_summary(response):
    """Return a compact response summary for assertion messages."""
    return f"status={response.status_code}, body={response.text[:1000]}"


def assert_api_response(
    response,
    expected_statuses=("success",),
    expected_data_type=None,
    expected_data_keys=None,
):
    """Validate the standard API response envelope and optional data shape."""
    assert response.content, response_summary(response)
    payload = json_payload(response)
    assert isinstance(payload, dict), response_summary(response)

    if "status" not in payload:
        return payload

    assert payload["status"] in expected_statuses, response_summary(response)
    assert isinstance(payload.get("code"), int), response_summary(response)
    assert "message" in payload, response_summary(response)
    assert "data" in payload, response_summary(response)

    data = payload["data"]
    if payload["status"] == "success":
        if expected_data_type is not None:
            assert isinstance(data, expected_data_type), response_summary(response)
        if expected_data_keys is not None:
            assert isinstance(data, dict), response_summary(response)
            for key in expected_data_keys:
                assert key in data, response_summary(response)
    else:
        assert isinstance(payload.get("errors", []), list), response_summary(response)
    return data


def assert_success_response(response, expected_data_type=None, expected_data_keys=None):
    """Validate a successful standard API response."""
    assert response.status_code == 200, response_summary(response)
    return assert_api_response(
        response,
        expected_statuses=("success",),
        expected_data_type=expected_data_type,
        expected_data_keys=expected_data_keys,
    )


def assert_cmfquery_response(response, expected_data_type=None, expected_data_keys=None):
    """Validate a CMFQuery endpoint response, including success and error envelopes."""
    assert response.status_code == 200, response_summary(response)
    return assert_api_response(
        response,
        expected_statuses=("success", "error", "partial"),
        expected_data_type=expected_data_type,
        expected_data_keys=expected_data_keys,
    )


def _cmf_failure_message(result):
    # Check if the result indicates a CMF failure based on known prefixes or substrings.
    if result is None:
        return "returned None"
    result_str = str(result)
    if any(result_str.startswith(p) for p in _CMF_FAILURE_PREFIXES):
        return result_str
    if any(sub in result_str for sub in _CMF_FAILURE_SUBSTRINGS):
        return result_str
    return None


def assert_cmf_success(result, operation: str = ""):
    """Fail the test if the CMF operation returned a failure message.

    CMF wrapper functions (cmf.artifact_push, cmf.metadata_push, etc.) catch
    internal CmfFailure exceptions and return their message as a plain string
    instead of raising. This helper re-surfaces those failures as test failures.
    """
    failure_message = _cmf_failure_message(result)
    if failure_message:
        label = f"{operation}: " if operation else ""
        pytest.fail(f"{label}{failure_message}")


def fail_cmf_init(backend: str, message: str):
    """Record failed cmf init for a backend and fail the init test."""
    _CMF_INIT_STATUS[backend] = False
    pytest.fail(message)


def assert_cmf_init_success(result, backend: str, operation: str = "cmf_init"):
    """Record cmf init status and fail when init returns a CMF failure string."""
    failure_message = _cmf_failure_message(result)
    if failure_message:
        _CMF_INIT_STATUS[backend] = False
        label = f"{operation}: " if operation else ""
        pytest.fail(f"{label}{failure_message}")
    _CMF_INIT_STATUS[backend] = True


def require_cmf_init_success(backend: str):
    """Fail downstream tests when cmf init did not complete successfully."""
    if _CMF_INIT_STATUS.get(backend) is not True:
        pytest.fail(f"cmf init for {backend} did not complete successfully.")