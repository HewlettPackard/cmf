import pytest
import subprocess
from cmflib import cmf	
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

def server_start():
    compose_file_path = '/home/chobey/testing/cmf/docker-compose-server.yml'
    server_process=  subprocess.run(['docker','compose', '-f', compose_file_path, 'up','-d'], check=True,env={'IP':'10.93.244.206' })
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
     
class TestClass:
    def test_cmf_init_show(self):
        _=cmf.cmf_init_show()
        print("___________________________________________________________")
    
#    def test_cmf_init_minios3(self):
#        _=cmf.cmf_init(type="minioS3",url="s3://bucket-name",endpoint_url="http://localhost:9000",access_key_id="minioadmin",secret_key="minioadmin",git_remote_url="https://github.com")
#        print("___________________________________________________________")

#    def test_cmf_init_amazonS3(self):
#        _=cmf.cmf_init(type="amazonS3",url="s3://bucket-name",endpoint_url="http://localhost:9000",access_key_id="minioadmin",secret_key="minioadmin",git_remote_url="https://github.com")
#        print("___________________________________________________________")

#    def test_cmf_init_sshremote(self):
#        _=cmf.cmf_init(type="sshremote",path="/home/user/local-storage",user="abhi",port="22",password="user",git_remote_url="https://github.com")
#        print("___________________________________________________________")

    def test_cmf_init_local(self):
        _=cmf.cmf_init(type="local",path="/home/chobey/local-storage",git_remote_url="https://github.com",neo4j_user='neo4j',neo4j_password="Abhinav@2021",neo4j_uri="bolt://10.93.244.206:7687",cmf_server_url="http://10.93.244.206:8080")
        print("___________________________________________________________")

class TestCommands:
    try:
        script_name='test_script.sh'
        subprocess.run(['chmod','+x',script_name],check=True)
        subprocess.run(['./',script_name], check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
    else:
        print(f"{script_name} executed successfully.")

    def test_metadata_push(self,start_server):
        _=cmf.metadata_push(pipeline_name="Test-env",filename="/home/chobey/testing/testenv/example-get-started/mlmd")
        print("___________________________________________________________")

    def test_metadata_pull(self,start_server):
        _=cmf.metadata_pull(pipeline_name="Test-env",filename="./mlmd")
        print("___________________________________________________________")

    def test_artifact_push(self):
        _=cmf.artifact_push()
        print("___________________________________________________________")

#    def test_artifact_pull(self):
#        _=cmf.artifact_pull(pipeline_name="Test-env",filename="./mlmd")
#        print("___________________________________________________________")

    def test_artifact_pull_single(self):
        _=cmf.artifact_pull_single(pipeline_name="Test-env",filename="./mlmd",artifact_name="data.xml.gz")
        print("___________________________________________________________")



     
