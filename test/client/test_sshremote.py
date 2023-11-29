import pytest
import subprocess
import time
import os
from cmflib import cmf

def test_cmf_init_show():
    print()
    print("-------------------------------Test Case Name: cmf init show ----------------------------------")
    _= cmf.cmf_init_show()


def test_cmf_init_sshremote(cmf_server_url, ssh_user, ssh_pass, ssh_path):
    print("-------------------------------Test Case Name: cmf init sshremote ----------------------------------")
    _=cmf.cmf_init(type="sshremote", path=ssh_path, user=ssh_user, port="22", password=ssh_pass,
                      git_remote_url="https://github.com/user-hpe/experiment-repo.git", cmf_server_url=cmf_server_url)

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



