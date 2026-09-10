###
# Copyright (2024) Hewlett Packard Enterprise Development LP
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
import json
from pathlib import Path

_CONFIG_JSON = Path(__file__).parent.parent / "config.json"


def _server_reachable():
    """Return True if the cmf-server API responds at /api/pipelines."""
    try:
        with open(str(_CONFIG_JSON), 'r') as f:
            data = json.load(f)
        url = data.get("cmf_server_url", "").rstrip("/")
        if not url:
            return False
        response = requests.get(f"{url}/api/pipelines", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(autouse=True)
def require_server():
    """
    Runtime guard: skip any server test if cmf-server is not reachable.

    This runs just before each test, so it correctly handles both cases:
    - Server was already running when pytest started.
    - Server was started by the start_server fixture during client tests
      (session-scoped, so it is up before server tests execute).
    """
    if not _server_reachable():
        pytest.skip("cmf-server not reachable")

