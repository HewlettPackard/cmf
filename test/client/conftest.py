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
import requests

@pytest.fixture(scope="module")
def start_server():
    # Specify the path to your JSON file
    json_file_path = '../config.json'

   # Open the file for reading
    with open(json_file_path, 'r') as file:
        # Load the JSON data from the file
         data = json.load(file)

    url = data.get("cmf_server_url", "http://127.0.0.1:80")

    # Ports to check
    ports_to_check = [80, 3000]

    # Check if ports are in use
    for port in ports_to_check:
        if check_port_in_use(port):
            print(f"Port {port} is in use.")
            stop()
        else:
            print(f"Port {port} is not in use.")

    start(url)

@pytest.fixture(scope="module")
def stop_server():
    yield
    stop()

def stop():
    compose_file_path = "../../docker-compose-server.yml"
    command = f"docker compose -f {compose_file_path} stop"
    server_process =  subprocess.run(command, check=True, shell=True,  capture_output=True)


def start(url):
    compose_file_path = "../../docker-compose-server.yml"
    ip = url.split(":")[1].split("/")[2]
    command = f"IP={ip} docker compose -f {compose_file_path} up -d"
    server_process =  subprocess.run(command, check=True, shell=True,  capture_output=True)
    print("cmf server is starting.")
    if url_exists(url):
        print("server started")
    else:
        timeout = 120
        while timeout > 0 and not url_exists(url):
             time.sleep(1)
             timeout -= 1
    if url_exists(url):
        print("server started")
    else:
        print("couldn't start server")

def url_exists(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True  # URL exists
        else:
            return False  # URL exists, but the response status code is not 200
    except requests.ConnectionError:
        return False  # URL doesn't e

def pytest_addoption(parser):
    parser.addoption(
        "--cmf_server_url",
        action="append",
        default=[],
        help="pass cmf_server_url to test functions",
    )
    parser.addoption(
        "--ssh_path",
        action="append",
        default=[],
        help="pass ssh remote path to test ssh functionality",
    )

    parser.addoption(
        "--ssh_user",
        action="append",
        default=[],
        help="pass ssh remote user to test ssh functionality",
    )

    parser.addoption(
        "--ssh_pass",
        action="append",
        default=[],
        help="pass ssh remote pass to test ssh functionality",
    )



def pytest_generate_tests(metafunc):
    if "cmf_server_url" in metafunc.fixturenames:
        metafunc.parametrize("cmf_server_url", metafunc.config.getoption("cmf_server_url"))
    if "ssh_path" in metafunc.fixturenames:
        metafunc.parametrize("ssh_path", metafunc.config.getoption("ssh_path"))
    if "ssh_user" in metafunc.fixturenames:
        metafunc.parametrize("ssh_user", metafunc.config.getoption("ssh_user"))
    if "ssh_pass" in metafunc.fixturenames:
        metafunc.parametrize("ssh_pass", metafunc.config.getoption("ssh_pass"))


def check_port_in_use(port):
    """Check if a given port is in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

@pytest.fixture(scope="module")
def start_minio_server():
    # Specify the path to your JSON file
    json_file_path = '../config.json'

   # Open the file for reading
    with open(json_file_path, 'r') as file:
        # Load the JSON data from the file
         data = json.load(file)

    url = data.get("cmf_server_url", "http://127.0.0.1")

    # Ports to check
    ports_to_check = [9000]

    # Check if ports are in use
    for port in ports_to_check:
        if check_port_in_use(port):
            print(f"Port {port} is in use.")
            minio_stop()
        else:
            print(f"Port {port} is not in use.")

    minio_start(url)


def minio_start(url):
    compose_file_path = os.path.join(os.getcwd(), 'docker-compose.yml')
    ip = url.split(":")[1].split("/")[2]
    command = f"IP={ip} docker compose -f {compose_file_path} up -d"
    server_process =  subprocess.run(command, check=True, shell=True,  capture_output=True)
    #end_url = f"http://{ip}:9000/minio/login"
    print("minio server is starting.")
    # Port to check
    port = 9000

    timeout = 120
    while timeout > 0 and not check_port_in_use(port):
         time.sleep(1)
         timeout -= 1
    if check_port_in_use(port):
            print(f"minioS3 server started")
    else:
        print(f"couldn't start minioS3 server.")
        sys.exit(1)



@pytest.fixture(scope="module")
def stop_minio_server():
    yield
    minio_stop()

def minio_stop():
    compose_file_path = os.path.join(os.getcwd(), 'docker-compose.yml')
    command = f"docker compose -f {compose_file_path} stop"
    server_process =  subprocess.run(command, check=True, shell=True,  capture_output=True)

