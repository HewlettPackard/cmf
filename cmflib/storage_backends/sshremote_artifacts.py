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

# this is temporary - need to remove after TripleDES warning goes away from paramiko
import warnings
warnings.filterwarnings(action='ignore', module='.*paramiko.*')

class SSHremoteArtifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        host: str,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        user = dvc_config_op["remote.ssh-storage.user"]
        password = dvc_config_op["remote.ssh-storage.password"]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )  # this can lead to man in the middle attack, need to find another solution
            ssh.connect(host, username=user, password=password)
            sftp = ssh.open_sftp()
            dir_path = ""
            # in case download_loc is absolute path like home/user/test/data.xml.gz
            # we need to make this absolute path a relative one by removing first '/'
            if os.path.isabs(download_loc):
                download_loc = download_loc[1:]
            if "/" in download_loc:
                dir_path, _ = download_loc.rsplit("/", 1)
            if dir_path != "":
                # creates subfolders needed as per artifacts' folder structure
                os.makedirs(dir_path, mode=0o777, exist_ok=True) 

            response = ""
            abs_download_loc = os.path.abspath(os.path.join(current_directory, download_loc))
            """"
            if object_name ends with .dir - it is a directory.
            we download .dir object with 'temp_dir' and remove 
            this after all the files from this .dir object is downloaded.
            """
            if object_name.endswith('.dir'):
                # in case of .dir, abs_download_loc is a absolute path for a folder
                os.makedirs(abs_download_loc, mode=0o777, exist_ok=True)

                 # download .dir object
                temp_dir = f"{abs_download_loc}/temp_dir"
                response = sftp.put(object_name, temp_dir)

                with open(temp_dir, 'r') as file:
                    tracked_files = eval(file.read())

                # removing temp_dir
                if os.path.exists(temp_dir):
                    os.remove(temp_dir)

                """
                object_name =  /home/user/ssh-storage/files/md5/dd/2d792b7cf6efb02231f85c6147e403.dir
                contains the path of the .dir on the artifact repo
                we need to remove the hash of the .dir from the object_name
                which will leave us with the artifact repo path
                """
                repo_path = "/".join(object_name.split("/")[:-2])
                for file_info in tracked_files:
                    relpath = file_info['relpath']
                    md5_val = file_info['md5']
                    # download_loc =  /home/user/datatslice/example-get-started/test/artifacts/raw_data
                    # md5_val = a237457aa730c396e5acdbc5a64c8453
                    # we need a2/37457aa730c396e5acdbc5a64c8453
                    formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                    temp_download_loc = f"{abs_download_loc}/{relpath}"
                    temp_object_name = f"{repo_path}/{formatted_md5}"
                    obj = sftp.put(object_name, temp_download_loc)
                    if obj:
                        print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
            else:
                response = sftp.put(object_name, abs_download_loc)
            if response:
                stmt = f"object {object_name} downloaded at {abs_download_loc}."
                return stmt

            sftp.close()
            ssh.close()

        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
