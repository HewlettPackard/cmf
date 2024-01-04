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

import requests
import json

# This function posts mlmd data to mlmd_push api on cmf-server
def call_mlmd_push(json_payload, url, exec_id):
    url_to_pass = f"{url}/mlmd_push"
    json_data = {"id": exec_id, "json_payload": json_payload}
    response = requests.post(url_to_pass, json=json_data)  # Post request
    # print("Status code -", response.status_code)
    return response


# This function gets mlmd data from mlmd_pull api from cmf-server
def call_mlmd_pull(url, pipeline_name, exec_id):
    url_to_pass = f"{url}/mlmd_pull/{pipeline_name}"
    response = requests.get(url_to_pass, json={"exec_id": exec_id})  # Get request
    return response
