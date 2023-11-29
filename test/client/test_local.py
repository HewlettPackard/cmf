import pytest
import subprocess
import time
import os
from cmflib import cmf

def test_cmf_init_show():
    print()
    print("-------------------------------Test Case Name: cmf init show ----------------------------------")
    _= cmf.cmf_init_show()


def test_cmf_init_local(cmf_server_url):
    print("-------------------------------Test Case Name: cmf init local ----------------------------------")
    path = f"{os.getcwd()}/local-storage"
    _ = cmf.cmf_init(type="local", path=path, git_remote_url="https://github.com/user-hpe/experiment-repo.git",
               neo4j_user='neo4j', neo4j_password="xxxxxx", neo4j_uri="bolt://xx.xx.xxx.xxx:7687", cmf_server_url=cmf_server_url)


def test_script():
    print("-------------------------------Test Case Name: Run sample test_script.sh ----------------------------------")
    cur_dir = os.getcwd()
    script_name = cur_dir + '/test_script.sh'
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


def test_artifact_push():
    print("-------------------------------Test Case Name: cmf artifact push ----------------------------------")
    _= cmf.artifact_push()


def test_metadata_push(start_server):
    print("-------------------------------Test Case Name: cmf metadata push  ----------------------------------")
    _= cmf.metadata_push(pipeline_name="Test-env", filename="mlmd")


def test_metadata_pull(stop_server):
    print("-------------------------------Test Case Name: cmf metadata pull  ----------------------------------")
    os.makedirs("./pull", exist_ok=True)
    _=cmf.metadata_pull(pipeline_name="Test-env",filename="./pull/mlmd")

def test_artifact_pull():
    print("-------------------------------Test Case Name: cmf artifact pull  ----------------------------------")
    _=cmf.artifact_pull(pipeline_name="Test-env",filename="./pull/mlmd")

def test_artifact_pull_single():
    print("-------------------------------Test Case Name: cmf artifact pull single artifact  ----------------------------------")
    _=cmf.artifact_pull_single(pipeline_name="Test-env",filename="./pull/mlmd",artifact_name="data.xml.gz")
