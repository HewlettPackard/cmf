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

import subprocess
import os
import sys


def fix_subparsers(subparsers):
    subparsers.required = True
    subparsers.dest = "cmd"

def git_exists():
    try:
        output = subprocess.check_output(["git", "version"]).decode("ascii")
        return output
    except FileNotFoundError:
        return "ERROR: git is not installed!! Install git."


def find_root(file_name: str):
    """This function returns the root of the file passed as a parameter.
    It searches for the file in the parent directory until the mount
    if it is not in the current directory.
    """
    msg = "'cmf' is not configured.\nExecute 'cmf init' command."
    # make current directory as root directory
    root_dir = os.path.realpath(os.getcwd())
    while True:
        # adding file name to the root directory
        file_path = os.path.join(root_dir, file_name)
        # whether file path exists, if yes return function with root_dir
        if os.path.exists(file_path):
            return root_dir
        # as file doesn't exists in root_dir and if root_dir is mount directory return msg
        if os.path.ismount(root_dir):
            return msg
        # assigning parent of root_dir
        parent = os.path.abspath(os.path.join(root_dir, os.pardir))
        # updating root_dir with its parent
        root_dir = parent


def check_minio_server(dvc_config_op):
    from minio import Minio
    from minio.error import S3Error

    if dvc_config_op["core.remote"] == "minio":
        endpoint = dvc_config_op["remote.minio.endpointurl"].split("http://")[1]
        access_key = dvc_config_op["remote.minio.access_key_id"]
        secret_key = dvc_config_op["remote.minio.secret_access_key"]
        bucket_name = dvc_config_op["remote.minio.url"].split("s3://")[1]
        try:
            client = Minio(
                endpoint, access_key=access_key, secret_key=secret_key, secure=False
            )
            found = client.bucket_exists(bucket_name)
            if found:
                return "SUCCESS"
        except TypeError as exception:
            return exception
        except S3Error as exception:
            return exception


