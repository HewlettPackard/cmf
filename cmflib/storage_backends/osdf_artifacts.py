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
import requests
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class OSDFremoteArtifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        host: str, #s_url 
        current_directory: str, #current_directory where cmf artifact pull is executed
        remote_file_path: str, # download_loc of the artifact 
        local_path: str, #name of the artifact
    ):
        output = ""
        remote_repo = dvc_config_op["remote.osdf.url"]
        user = "nobody"
        dynamic_password = dvc_config_op["remote.osdf.password"]
        custom_auth_header = dvc_config_op["remote.osdf.custom_auth_header"]
        #print(f"dynamic password from download_artifacts={dynamic_password}")
        #print(f"Fetching artifact={local_path}, surl={host} to {remote_file_path} when this has been called at {current_directory}")

        try:
            headers={dvc_config_op["remote.osdf.custom_auth_header"]: dvc_config_op["remote.osdf.password"]}
            temp = local_path.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            dir_to_create = os.path.join(current_directory, dir_path)
            os.makedirs(
                dir_to_create, mode=0o777, exist_ok=True
            )  # creates subfolders needed as per artifacts folder structure
            local_file_path = os.path.join(current_directory, local_path)
            local_file_path = os.path.abspath(local_file_path)

            response = requests.get(host, headers=headers, verify=True) #This should be made True. otherwise this will produce Insecure SSL Warning
            if response.status_code == 200 and response.content:
                data = response.content
            else:
                return "No data received from the server."

        except Exception as exception:
            return exception

        try:
            with open(remote_file_path, 'wb') as file:
                file.write(data)
            if os.path.exists(remote_file_path) and os.path.getsize(remote_file_path) > 0:
                #print(f"object {local_path} downloaded at {remote_file_path}")
                stmt = f"object {local_path} downloaded at {remote_file_path}."
                return stmt
        except Exception as e:
            print(f"An error occurred while writing to the file: {e}")
