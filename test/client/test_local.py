import pytest
import subprocess
from cmflib import cmf	
import time
import os
from cmflib.cli.utils import find_root
from cmflib.utils.cmf_config import CmfConfig
import requests

class TestClass:
    def test_cmf_init_show(self):
        _=cmf.cmf_init_show()
        print("___________________________________________________________")
    
    def test_cmf_init_local(self):
        _=cmf.cmf_init(type="local",path="/home/user/local-storage",git_remote_url="https://github.com",neo4j_user='neo4j',neo4j_password="xxxxxx",neo4j_uri="bolt://xx.xx.xxx.xxx:7687",cmf_server_url="http://xx.xx.xxx.xxx:8080")
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

    def test_artifact_push(self):
        _=cmf.artifact_push()
        print("___________________________________________________________")

#    def test_artifact_pull(self):
#        _=cmf.artifact_pull(pipeline_name="Test-env",filename="./mlmd")
#        print("___________________________________________________________")

    def test_artifact_pull_single(self):
        _=cmf.artifact_pull_single(pipeline_name="Test-env",filename="./mlmd",artifact_name="data.xml.gz")
        print("___________________________________________________________")



     
