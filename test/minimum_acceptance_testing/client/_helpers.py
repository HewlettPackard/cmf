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


def assert_cmf_success(result, operation: str = ""):
    """Fail the test if the CMF operation returned a failure message.

    CMF wrapper functions (cmf.artifact_push, cmf.metadata_push, etc.) catch
    internal CmfFailure exceptions and return their message as a plain string
    instead of raising. This helper re-surfaces those failures as test failures.
    """
    if result is None:
        pytest.fail(f"{operation}: returned None".strip())
        return
    result_str = str(result)
    if any(result_str.startswith(p) for p in _CMF_FAILURE_PREFIXES):
        label = f"{operation}: " if operation else ""
        pytest.fail(f"{label}{result_str}")
    if any(sub in result_str for sub in _CMF_FAILURE_SUBSTRINGS):
        label = f"{operation}: " if operation else ""
        pytest.fail(f"{label}{result_str}")
