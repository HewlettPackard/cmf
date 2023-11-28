import pytest
import psutil
import subprocess
import time
import os
import json

@pytest.fixture(scope="module")
def start_server():
    # Specify the path to your JSON file
    json_file_path = '../config.json'

   # Open the file for reading
    with open(json_file_path, 'r') as file:
        # Load the JSON data from the file
         data = json.load(file)

    url = data.get("cmf_server_url", "http://127.0.0.1:8080")
    print(url)

    # Ports to check
    ports_to_check = [8080, 3000]

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
        print("server started")
    if timeout < 0 :
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
        action="store",
        default="",
        help="pass cmf_server_url to test functions",
    )
    parser.addoption(
        "--ssh_path",
        action="store",
        default="",
        help="pass ssh remote path to test ssh functionality",
    )

    parser.addoption(
        "--ssh_user",
        action="store",
        default="",
        help="pass ssh remote user to test ssh functionality",
    )

    parser.addoption(
        "--ssh_pass",
        action="store",
        default="",
        help="pass ssh remote pass to test ssh functionality",
    )



def pytest_generate_tests(metafunc):
    if "cmf_server_url" in metafunc.fixturenames:
        metafunc.parametrize("cmf_server_url", metafunc.config.getoption("cmf_server_url"))
    if "ssh_path" in metafunc.fixturenames:
        metafunc.parametrize("ssh_path", metafunc.config.getoption("ssh_path"))
    if "ssh_user" in metafunc.fixturenames:
        metafunc.parametrize("ssh_path", metafunc.config.getoption("ssh_user"))
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

    url = data.get("cmf_server_url", "http://127.0.0.1:8080")
    print(url)

    # Ports to check
    ports_to_check = [9000]

    # Check if ports are in use
    for port in ports_to_check:
        if check_port_in_use(port):
            print(f"Port {port} is in use.")
            stop()
        else:
            print(f"Port {port} is not in use.")

    start_minio(url)


def minio_start(url):
    compose_file_path = './docker-compose.yml'
    ip = url.split(":")[1].split("/")[2]
    command = f"IP={ip} docker compose -f {compose_file_path} up -d"
    server_process =  subprocess.run(command, check=True, shell=True,  capture_output=True)
    url = f"http://{ip}:9000"
    print("minio server is starting.")
    if url_exists(url):
        print("server started")
    else:
        timeout = 120
        while timeout > 0 and not url_exists(url):
             time.sleep(1)
             timeout -= 1
        print("server started")
    if timeout < 0 :
        print("couldn't start server")

@pytest.fixture(scope="module")
def stop_minio_server():
    yield
    minio_stop()

def minio_stop():
    compose_file_path = "../../docker-compose-server.yml"
    command = f"docker compose -f {compose_file_path} stop"
    server_process =  subprocess.run(command, check=True, shell=True,  capture_output=True)

