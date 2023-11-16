import pytest
import subprocess
from cmflib import cmf	
import os
from cmflib.cli.utils import find_root
from cmflib.utils.cmf_config import CmfConfig
import requests
import time

@pytest.fixture(scope="module")
def start_minio_server():
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
    url = attr_dict.get("endpointurl", "http://127.0.0.1:9000")
    if url_exists(url):
        subprocess.run(['docker','stop', 's3','aws-cli'], check=True)
        subprocess.run(['docker','rm', 's3','aws-cli'], check=True)
        subprocess.run(['docker','image','rm','amazon/aws-cli:latest','minio/minio:RELEASE.2021-02-11T08-23-43Z'], check=True)
        minio_server_start()
    else:
        minio_server_start()
    if url_exists(url):
        return
    else:
        return "server is down"

def minio_server_start():
    compose_file_path = '/home/user/example-get-started/docker-compose.yml'
    server_process=  subprocess.run(['docker','compose', '-f', compose_file_path, 'up','-d'], check=True,env={'MYIP':'10.93.244.206' })
    print("Docker Compose services have been started.")
    timeout = 120  
    while timeout > 0:
        time.sleep(1)
        timeout -= 1

class TestClass:
    def test_cmf_init_show(self):
        _=cmf.cmf_init_show()
        print("___________________________________________________________")
    
    def test_cmf_init_minios3(self):
        _=cmf.cmf_init(type="minioS3",url="s3://dvc-art",endpoint_url="http://xx.xx.xxx.xxx:9000",access_key_id="xxxxxx",secret_key="xxxxxx",git_remote_url="https://github.com",cmf_server_url="http://xx.xx.xxx.xxx:8080")
        print("___________________________________________________________")

class TestCommands:
    def test_script(self):
        script_name='./test_script.sh'
        try:
            subprocess.run(['chmod','+x',script_name],check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error setting execute permission for {script_name}: {e}")
        else:
            try:
                subprocess.run([script_name], check=True, shell=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running {script_name}: {e}")
            else:
                print(f"{script_name} executed successfully.")

    def test_metadata_push(self,start_server):
        _=cmf.metadata_push(pipeline_name="Test-env",filename="/home/user/example-get-started/mlmd")
        print("___________________________________________________________")

    def test_metadata_pull(self,stop_server):
        _=cmf.metadata_pull(pipeline_name="Test-env",filename="./mlmd")
        print("___________________________________________________________")

    def test_artifact_push(self,start_minio_server):
        _=cmf.artifact_push()
        print("___________________________________________________________")
    
    def test_artifact_pull(self,start_minio_server):
        _=cmf.artifact_pull(pipeline_name="Test-env",filename="./mlmd")
        print("___________________________________________________________")

    '''
    def test_artifact_pull_single(self,start_minio_server):
        _=cmf.artifact_pull_single(pipeline_name="Test-env",filename="./mlmd",artifact_name="data.xml.gz")
        print("___________________________________________________________")
    '''
