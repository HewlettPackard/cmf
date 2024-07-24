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
            # download_loc = contains absolute path of the file with file name and extension
            temp = download_loc.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            os.makedirs(dir_path, mode=0o777, exist_ok=True) # creating subfolders
            if current_loc.endswith('.dir'):
                # in case of .dir, download_loc is a absolute path for a folder
                os.makedirs(download_loc, mode=0o777, exist_ok=True)
                # download the .dir file
                temp_dir = f"{download_loc}/dir"
                fs.get_file(current_loc, temp_dir)
                with open(temp_dir, 'r') as file:
                    tracked_files = eval(file.read())
                """
                current_loc = "files/md5/9b/9a458ac0b534f088a47c2b68bae479.dir" 
                contains the path of the .dir on the artifact repo
                we need to remove the hash of the .dir from the current_loc 
                which will leave us with the artifact repo path
                """
                repo_path = current_loc.split("/")
                repo_path = repo_path[:len(repo_path)-2]
                repo_path = "/".join(repo_path)
                for file_info in tracked_files:
                    relpath = file_info['relpath']
                    md5_val = file_info['md5']
                    # md5_val = a237457aa730c396e5acdbc5a64c8453
                    # we need a2/37457aa730c396e5acdbc5a64c8453
                    formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                    temp_download_loc = f"{download_loc}/{relpath}"
                    temp_current_loc = f"{repo_path}/{formatted_md5}"
                    obj = fs.get_file(temp_current_loc, temp_download_loc)
                    if obj == None: 
                        print(f"object {temp_current_loc} downloaded at {temp_download_loc}.")
                if os.path.exists(temp_dir):
                    os.remove(temp_dir)
            else:
                obj = fs.get_file(current_loc, download_loc)
            if obj == None:  # get_file() returns none when file gets downloaded.
                stmt = f"object {current_loc} downloaded at {download_loc}."
                return stmt
        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
