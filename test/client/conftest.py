import pytest
import subprocess
import time
import os
from cmflib.cli.utils import find_root
from cmflib.utils.cmf_config import CmfConfig
import requests

@pytest.fixture(scope="module")
def start_server():
    # Define the path to your Docker Compose file
    server=0

    cmfconfig = os.environ.get("CONFIG_FILE",".cmfconfig")

    # find root_dir of .cmfconfig
    output = find_root(cmfconfig)

    # in case, there is no .cmfconfig file
    if output.find("'cmf' is  not configured") != -1:
        return output

    config_file_path = os.path.join(output, cmfconfig)

    attr_dict = CmfConfig.read_config(config_file_path)
    url = attr_dict.get("cmf-server-ip", "http://127.0.0.1:80")
    if url_exists(url):
        subprocess.run(['docker','stop', 'cmf-server','ui-server'], check=True)
        subprocess.run(['docker','rm', 'cmf-server','ui-server'], check=True)
        subprocess.run(['docker','image','rm','server:latest','ui:latest'], check=True)
        server_start()
    else:
        server_start()
    if url_exists(url):
        return
    else:
        return "server is down"
    
@pytest.fixture(scope="module")
def stop_server():
    yield
    subprocess.run(['docker','stop', 'cmf-server','ui-server'], check=True)
    subprocess.run(['docker','rm', 'cmf-server','ui-server'], check=True)
    subprocess.run(['docker','image','rm','server:latest','ui:latest'], check=True)

def server_start():
    compose_file_path = '/home/chobey/testing/cmf/docker-compose-server.yml'
    server_process=  subprocess.run(['docker','compose', '-f', compose_file_path, 'up','-d'], check=True,env={'IP':'xx.xx.xxx.xxx' })
    print("Docker Compose services have been started.")
    timeout = 120  
    while timeout > 0:
        time.sleep(1)
        timeout -= 1

def url_exists(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True  # URL exists
        else:
            return False  # URL exists, but the response status code is not 200
    except requests.ConnectionError:
        return False  # URL doesn't e
