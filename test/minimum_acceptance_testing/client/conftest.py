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
import psutil
import subprocess
import time
import os
import json
import shutil
import requests
from pathlib import Path

_CLIENT_DIR            = Path(__file__).parent          # test/mat/client/
_MAT_DIR               = _CLIENT_DIR.parent             # test/mat/
_CMF_DIR               = _MAT_DIR.parent.parent         # cmf/
CONFIG_JSON            = _MAT_DIR / "config.json"
_EXAMPLE_SRC           = _CMF_DIR / "examples" / "example-get-started"
_DOCKER_COMPOSE_SERVER = _CMF_DIR / "docker-compose-server.yml"
_MLMD_PATH             = _MAT_DIR.parent / "cmf-server" / "data" / "mlmd"


@pytest.fixture(scope="module")
def example_workspace(tmp_path_factory):
    """
    Copies example-get-started to a temp directory and chdirs into it.
    All client tests that use this fixture run from inside that directory.
    Restores the original directory and cleans up after the module.
    """
    dest = tmp_path_factory.mktemp("workspace") / "example-get-started"
    shutil.copytree(str(_EXAMPLE_SRC), str(dest))
    original_dir = os.getcwd()
    os.chdir(str(dest))
    yield str(dest)
    os.chdir(original_dir)
    # clean up mlmd pushed to server during the test run
    if _MLMD_PATH.exists():
        subprocess.run(["sudo", "rm", "-rf", str(_MLMD_PATH)], check=False)


# Tracks whether the MAT framework started the server itself.
# If the server was already running when the tests began, we leave it running after.
_server_started_by_mat = False


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


def _stop():
    command = f"docker compose -f {str(_DOCKER_COMPOSE_SERVER)} stop"
    # No capture_output so docker stop messages are visible in terminal
    subprocess.run(command, check=True, shell=True)


def _start(url):
    ip = url.split(":")[1].split("/")[2]
    command = f"sudo IP={ip} docker compose -f {str(_DOCKER_COMPOSE_SERVER)} up -d"
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
    # Probe /api/pipelines (FastAPI backend) not / (nginx always returns 200 even when backend is down)
    try:
        response = requests.get(url.rstrip("/") + "/api/pipelines", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


def check_port_in_use(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

