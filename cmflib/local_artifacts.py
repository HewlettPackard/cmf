###
# Copyright (2022) Hewlett Packard Enterprise Development LP
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

from dvc.api import DVCFileSystem

class local_artifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        current_directory: str,
        current_dvc_loc: str,
        download_loc: str,
    ):
        obj = True
        try:
            fs = DVCFileSystem(dvc_config_op[1])
            temp = download_loc.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            dir_to_create = os.path.join(current_directory, dir_path)
            os.makedirs(dir_to_create, mode=0o777, exist_ok=True)
            obj = fs.get_file(current_dvc_loc, download_loc)
            if obj == None:
                stmt = f"object {current_dvc_loc} downloaded at {download_loc}."
                return stmt
        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
