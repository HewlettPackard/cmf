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

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
import requests

MAT_DIR     = Path(__file__).parent   # .../test/minimum_acceptance_testing/
TEST_DIR    = MAT_DIR.parent          # .../test/
CONFIG_JSON = MAT_DIR / "config.json" # runtime config: cmf_server_url, local_path, …
CMF_DIR               = MAT_DIR.parent.parent
EXAMPLE_SRC           = CMF_DIR / "examples" / "example-get-started"
DOCKER_COMPOSE_SERVER = CMF_DIR / "docker-compose-server.yml"
MLMD_PATH             = MAT_DIR.parent / "cmf-server" / "data" / "mlmd"
SERVER_TEST_DIR       = MAT_DIR / "server"

# Tracks whether the MAT framework started the server itself.
# If the server was already running when the tests began, we leave it running after.
_server_started_by_mat = False


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


@pytest.fixture(scope="module")
def example_workspace(tmp_path_factory):
    """
    Copies example-get-started to a temp directory and chdirs into it.
    All client tests that use this fixture run from inside that directory.
    Restores the original directory and cleans up after the module.
    """
    dest = tmp_path_factory.mktemp("workspace") / "example-get-started"
    shutil.copytree(str(EXAMPLE_SRC), str(dest))
    original_dir = os.getcwd()
    os.chdir(str(dest))
    yield str(dest)
    os.chdir(original_dir)
    # clean up mlmd pushed to server during the test run
    if MLMD_PATH.exists():
        subprocess.run(["sudo", "rm", "-rf", str(MLMD_PATH)], check=False)


@pytest.fixture(scope="session")
def start_server():
    global _server_started_by_mat
    with open(str(CONFIG_JSON), 'r') as file:
        data = json.load(file)
    url = data.get("cmf_server_url", "http://127.0.0.1:80")

    if _url_exists(url):
        print("cmf-server already running -- reusing existing server.")
        _server_started_by_mat = False
    else:
        print("cmf-server not running -- starting server.")
        _start(url)
        _server_started_by_mat = True


@pytest.fixture(scope="session")
def stop_server():
    yield
    # Only stop the server if the MAT framework started it; leave a user-managed server alone.
    # scope="session" ensures this teardown runs AFTER all tests (client + server) finish.
    if _server_started_by_mat:
        _stop()
    else:
        print("cmf-server was pre-existing -- leaving it running.")


@pytest.fixture(autouse=True)
def require_server(request):
    """
    Runtime guard: fail server tests if cmf-server is not reachable.

    This fixture is defined at the MAT root, so it is intentionally scoped by
    path and only guards tests under test/minimum_acceptance_testing/server/.
    Client tests must still be able to start the server themselves.
    """
    test_path = Path(str(request.node.fspath)).resolve()
    try:
        test_path.relative_to(SERVER_TEST_DIR.resolve())
    except ValueError:
        return
    if not _server_reachable():
        pytest.fail("cmf-server not reachable at configured cmf_server_url")


def _stop():
    command = f"docker compose -f {str(DOCKER_COMPOSE_SERVER)} stop"
    # No capture_output so docker stop messages are visible in terminal
    subprocess.run(command, check=True, shell=True)


def _start(url):
    ip = url.split(":")[1].split("/")[2]
    command = f"sudo IP={ip} docker compose -f {str(DOCKER_COMPOSE_SERVER)} up -d"
    # No capture_output — if docker fails, the error is printed to terminal
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        raise RuntimeError(
            "docker compose failed to start. Check the docker output above for details."
        )
    print("cmf server is starting.")
    timeout = 120
    while timeout > 0 and not _url_exists(url):
        time.sleep(1)
        timeout -= 1
    if _url_exists(url):
        print("server started")
    else:
        raise RuntimeError("cmf-server did not become reachable within 120 seconds.")


def _url_exists(url):
    # Probe /api/v1/pipelines (FastAPI backend) not / (nginx always returns 200 even when backend is down)
    try:
        response = requests.get(url.rstrip("/") + "/api/v1/pipelines", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


def _server_reachable():
    """Return True if the cmf-server API responds at /api/v1/pipelines."""
    try:
        with open(str(CONFIG_JSON), 'r') as f:
            data = json.load(f)
        url = data.get("cmf_server_url", "").rstrip("/")
        if not url:
            return False
        return _url_exists(url)
    except Exception:
        return False

