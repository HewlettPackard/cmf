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

import os
import paramiko


class SSHremoteArtifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        host: str,
        current_directory: str,
        remote_file_path: str,
        local_path: str,
    ):
        output = ""
        remote_repo = dvc_config_op["remote.ssh-storage.url"]
        user = dvc_config_op["remote.ssh-storage.user"]
        password = dvc_config_op["remote.ssh-storage.password"]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )  # this can lead to man in the middle attack, need to find another solution
            ssh.connect(host, username=user, password=password)
            sftp = ssh.open_sftp()
            temp = local_path.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            dir_to_create = os.path.join(current_directory, dir_path)
            os.makedirs(
                dir_to_create, mode=0o777, exist_ok=True
            )  # creates subfolders needed as per artifacts folder structure
            local_file_path = os.path.join(current_directory, local_path)
            local_file_path = os.path.abspath(local_file_path)
            output = sftp.put(remote_file_path, local_file_path)
            sftp.close()
            ssh.close()
            if output:
                stmt = f"object {remote_file_path} downloaded at {local_file_path}."
                return stmt

        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
