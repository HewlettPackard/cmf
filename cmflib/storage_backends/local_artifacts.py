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

from dvc.api import DVCFileSystem

class LocalArtifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        current_directory: str,
        current_loc: str,
        download_loc: str,
    ):
        obj = True
        try:
            fs = DVCFileSystem(
                dvc_config_op["remote.local-storage.url"]
            )  # dvc_config_op[1] is file system path - "/path/to/local/repository"
            # get_file() only creates file, to put artifacts in proper directory, subfolders are required.
            temp = download_loc.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            os.makedirs(dir_path, mode=0o777, exist_ok=True)  # creating subfolders
            obj = fs.get_file(current_loc, download_loc)
            if obj == None:  # get_file() returns none when file gets downloaded.
                stmt = f"object {current_loc} downloaded at {download_loc}."
                return stmt
        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
