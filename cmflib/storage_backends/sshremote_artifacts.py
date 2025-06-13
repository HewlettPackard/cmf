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

    def __init__(self, dvc_config_op):
        self.user = dvc_config_op["remote.ssh-storage.user"]
        self.password = dvc_config_op["remote.ssh-storage.password"]


    def download_file(
        self,
        host: str,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )  # this can lead to man in the middle attack, need to find another solution
        ssh.connect(host, username=self.user, password=self.password)
        sftp = ssh.open_sftp()
        dir_path = ""
        # in case download_loc is absolute path like /home/user/test/data.xml.gz
        # we need to make this absolute path a relative one by removing first '/'
        if os.path.isabs(download_loc):
            download_loc = download_loc[1:]
        if "/" in download_loc:
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            # creates subfolders needed as per artifacts' folder structure
            os.makedirs(dir_path, mode=0o777, exist_ok=True) 

        abs_download_loc = os.path.abspath(os.path.join(current_directory, download_loc))
        try:
            local_file_size = os.stat(object_name).st_size  # Get the size of the local file being uploaded
            # The put() method returns an SFTPAttributes object, which contains metadata about the uploaded file.
            # Therefore, response should be typed as SFTPAttributes.
            response: paramiko.SFTPAttributes = sftp.put(object_name, abs_download_loc)
            # we can close sftp connection as we have already downloaded the file
            sftp.close()
            ssh.close()
            # After upload, check if the uploaded file size matches the local file size
            if response.st_size == local_file_size:
                return object_name, abs_download_loc, True
            return  object_name, abs_download_loc, False
        except Exception as e:
            # this exception is for function sftp.put()
            sftp.close()
            ssh.close()
            return  object_name, abs_download_loc, False


    def download_directory(
        self,
        host: str,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )  # this can lead to man in the middle attack, need to find another solution
        ssh.connect(host, username=self.user, password=self.password)
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

        abs_download_loc = os.path.abspath(os.path.join(current_directory, download_loc))
                                               
        """"
        if object_name ends with .dir - it is a directory.
        we download .dir object with 'temp_dir' and remove 
        this after all the files from this .dir object is downloaded.
        """
        # in case of .dir, abs_download_loc is a absolute path for a folder
        os.makedirs(abs_download_loc, mode=0o777, exist_ok=True)

        # download .dir object
        temp_dir = f"{abs_download_loc}/temp_dir"
        try:
            # The put() method returns an SFTPAttributes object, which contains metadata about the uploaded file.
            # Therefore, response should be typed as SFTPAttributes.
            response: paramiko.SFTPAttributes = sftp.put(object_name, temp_dir)
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

            total_files_in_directory = 0
            files_downloaded = 0
            for file_info in tracked_files:
                total_files_in_directory += 1
                relpath = file_info['relpath']
                md5_val = file_info['md5']
                # download_loc =  /home/user/datatslice/example-get-started/test/artifacts/raw_data
                # md5_val = a237457aa730c396e5acdbc5a64c8453
                # we need a2/37457aa730c396e5acdbc5a64c8453
                formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                temp_download_loc = f"{abs_download_loc}/{relpath}"
                temp_object_name = f"{repo_path}/{formatted_md5}"
                try:
                    obj = sftp.put(object_name, temp_download_loc)
                    sftp.close()
                    ssh.close()
                    if obj:
                        files_downloaded += 1
                        print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
                    else:
                        print(f"object {temp_object_name} is not downloaded.")
                except Exception as e:
                    sftp.close()
                    ssh.close()
                    print(f"object {temp_object_name} is not downloaded.")

            # total_files - files_downloaded gives us the number of files which are failed to download
            if (total_files_in_directory - files_downloaded) == 0:   
                return total_files_in_directory, files_downloaded, True
            return total_files_in_directory, files_downloaded, False  
        except Exception as e:
            sftp.close()
            ssh.close()
            print(f"object {object_name} is not downloaded.")
            # We usually don't count .dir as a file while counting total_files_in_directory.
            # However, here we failed to download the .dir folder itself. 
            # So we need to make, total_files_in_directory = 1
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False
