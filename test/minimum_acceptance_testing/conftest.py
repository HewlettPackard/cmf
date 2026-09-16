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
import json
from pathlib import Path

MAT_DIR     = Path(__file__).parent   # .../test/minimum_acceptance_testing/
TEST_DIR    = MAT_DIR.parent          # .../test/
CONFIG_JSON = MAT_DIR / "config.json" # runtime config: cmf_server_url, local_path, …


def pytest_generate_tests(metafunc):
    """
    Inject 'cmf_server_url' into every test that declares it as a parameter.
    URL is read from config.json; falls back to http://127.0.0.1:80 if missing.
    """
    if "cmf_server_url" in metafunc.fixturenames:
        try:
            with open(str(CONFIG_JSON), 'r') as f:
                data = json.load(f)
            urls = [data.get("cmf_server_url", "http://127.0.0.1:80")]
        except Exception:
            urls = ["http://127.0.0.1:80"]
        metafunc.parametrize("cmf_server_url", urls)

