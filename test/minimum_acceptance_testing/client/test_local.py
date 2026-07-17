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
import subprocess
import time
import os
from cmflib import cmf
from cmflib.dvc_wrapper import check_git_remote, git_add_remote

pytestmark = pytest.mark.usefixtures("example_workspace")

def test_cmf_init_show():
    print()
    print("-------------------------------Test Case Name: cmf init show ----------------------------------")
    _= cmf.cmf_init_show()


def test_cmf_init_local(cmf_server_url):
    print("-------------------------------Test Case Name: cmf init local ----------------------------------")
    # local-storage can't be in the same folder where dvc was initialised
    path = f"{os.getcwd()}/../local-storage"
    git_remote_url = "https://github.com/hpe-user/experiment-repo.git"
    _ = cmf.cmf_init(type="local", path=path, git_remote_url=git_remote_url,
               neo4j_user='neo4j', neo4j_password="xxxxxx", neo4j_uri="bolt://xx.xx.xxx.xxx:7687", cmf_server_url=cmf_server_url)
    # cmf_init calls `git remote set-url cmf_origin` which silently fails when the
    # remote doesn't exist yet (the example workspace has no pre-existing cmf_origin).
    # Ensure the remote is set so downstream tests that call Cmf() pass the git-remote precheck.
    if not check_git_remote():
        git_add_remote(git_remote_url)


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
    _= cmf.artifact_push(pipeline_name="Test-env")


def test_metadata_push(start_server):
    print("-------------------------------Test Case Name: cmf metadata push  ----------------------------------")
    _= cmf.metadata_push(pipeline_name="Test-env", file_name="mlmd")


def test_metadata_pull(start_server, stop_server):
    print("-------------------------------Test Case Name: cmf metadata pull  ----------------------------------")
    _=cmf.metadata_pull(pipeline_name="Test-env", file_name="mlmd_pull")


def test_artifact_pull():
    print("-------------------------------Test Case Name: cmf artifact pull  ----------------------------------")
    _=cmf.artifact_pull(pipeline_name="Test-env", file_name="mlmd_pull")


def test_artifact_pull_single():
    print("-------------------------------Test Case Name: cmf artifact pull single artifact  ----------------------------------")
    _=cmf.artifact_pull(pipeline_name="Test-env", file_name="mlmd_pull", artifact_name="data.xml.gz")
