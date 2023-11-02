import pytest
import subprocess
from cmflib import cmf	


class TestClass:
    def test_cmf_init_show(self):
        _=cmf.cmf_init_show()
        print("___________________________________________________________")
    
    def test_cmf_init_minios3(self):
        _=cmf.cmf_init(type="minioS3",url="s3://bucket-name",endpoint_url="http://localhost:9000",access_key_id="minioadmin",secret_key="minioadmin",git_remote_url="https://github.com")
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

