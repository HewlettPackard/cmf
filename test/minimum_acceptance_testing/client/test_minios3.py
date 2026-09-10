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
import os
import json
import shutil
from pathlib import Path
from cmflib import cmf
from cmflib.dvc_wrapper import check_git_remote, git_add_remote
from _helpers import assert_cmf_success

_CONFIG_JSON = Path(__file__).parent.parent / "config.json"

pytestmark = pytest.mark.usefixtures("example_workspace")


def _get_config():
    with open(str(_CONFIG_JSON), "r") as f:
        return json.load(f)


def _require(data, key):
    val = data.get(key, "")
    if not val:
        pytest.fail(f"config.json: '{key}' is not set. Required for minioS3 backend.")
    return val


def test_cmf_init_minios3(cmf_server_url):
    print("-------------------------------Test Case Name: cmf init minioS3----------------------------------")
    data = _get_config()
    url          = _require(data, "minio_url")
    endpoint_url = _require(data, "minio_endpoint_url")
    access_key   = _require(data, "minio_access_key_id")
    secret_key   = _require(data, "minio_secret_key")
    git_remote_url = "https://github.com/hpe-user/experiment-repo.git"

    _ = cmf.cmf_init(
        type="minioS3",
        url=url,
        endpoint_url=endpoint_url,
        access_key_id=access_key,
        secret_key=secret_key,
        git_remote_url=git_remote_url,
        cmf_server_url=cmf_server_url,
    )
    if not check_git_remote():
        git_add_remote(git_remote_url)


def test_cmf_init_show():
    print()
    print("-------------------------------Test Case Name: cmf init show----------------------------------")
    _ = cmf.cmf_init_show()


def test_script():
    print("-------------------------------Test Case Name: Run sample test_script.sh----------------------------------")
    cur_dir = os.getcwd()
    script_name = cur_dir + "/test_script.sh"
    try:
        subprocess.run(["chmod", "+x", script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting execute permission for {script_name}: {e}")
    else:
        try:
            subprocess.run([script_name], check=True, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {script_name}: {e}")
        else:
            print(f"{script_name} executed successfully.")


def test_metadata_push(start_server):
    print("-------------------------------Test Case Name: cmf metadata push----------------------------------")
    result = cmf.metadata_push(pipeline_name="Test-env", file_name="mlmd")
    assert_cmf_success(result, "metadata_push")


def test_metadata_pull(start_server, stop_server):
    print("-------------------------------Test Case Name: cmf metadata pull----------------------------------")
    result = cmf.metadata_pull(pipeline_name="Test-env", file_name="mlmd_pull")
    assert_cmf_success(result, "metadata_pull")


def test_artifact_push():
    print("-------------------------------Test Case Name: cmf artifact push----------------------------------")
    result = cmf.artifact_push(pipeline_name="Test-env")
    assert_cmf_success(result, "artifact_push")


def test_artifact_pull():
    print("-------------------------------Test Case Name: cmf artifact pull----------------------------------")
    # MinioS3 pull uses the minio Python client directly (not DVC), so only the
    # DVC cache is cleared. Deleting artifacts/ would remove the download target
    # directory and cause fget_object to fail with a silent OSError.
    shutil.rmtree(".dvc/cache", ignore_errors=True)
    result = cmf.artifact_pull(pipeline_name="Test-env", file_name="mlmd")
    assert_cmf_success(result, "artifact_pull")


def test_artifact_pull_single():
    print("-------------------------------Test Case Name: cmf artifact pull single artifact----------------------------------")
    result = cmf.artifact_pull(pipeline_name="Test-env", file_name="mlmd", artifact_name="data.xml.gz")
    assert_cmf_success(result, "artifact_pull_single")
