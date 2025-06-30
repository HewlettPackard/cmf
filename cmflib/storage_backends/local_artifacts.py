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
# Error: Skipping analyzing "dvc.api": module is installed, but missing library stubs or py.typed marker
from dvc.api import DVCFileSystem    # type: ignore

class LocalArtifacts():
    """
        Initialize the LocalArtifacts class with local repo url.
        This class downloads one local artifact at a time and if the passed artifact is a directory 
        then, it downloads all the files from the directory 

        Args:
            dvc_config_op (dict): Dictionary containing local url (remote.local.url).
        """
    
    def __init__(self, dvc_config_op):
        self.fs = DVCFileSystem(
                dvc_config_op["remote.local-storage.url"]
            )  # dvc_config_op[1] is file system path - "/path/to/local/repository"
        
    def download_file(
        self,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        """
        Download a single file from an local repository.

        Args:
            current_directory (str): The current working directory.
            object_name (str): Key (path) of the file in the local repo.
            download_loc (str): Local path where the file should be downloaded.

        Returns:
            tuple: (object_name, download_loc, status) where status indicates success (True) or failure (False).
        """
        # get_file() only creates file, to put artifacts in proper directory, subfolders are required.
        # download_loc = contains absolute path of the file with file name and extension

        # Create necessary directories for the download location.
        dir_path = ""
        if "/" in download_loc:
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            os.makedirs(dir_path, mode=0o777, exist_ok=True)  # creating subfolders if needed
        
        try:
            # get_file() returns none when file gets downloaded.
            response = self.fs.get_file(object_name, download_loc)

            # Check if the response indicates success.
            if response == None:  
                return object_name, download_loc, True
            return  object_name, download_loc, False
        except Exception as e:
            return  object_name, download_loc, False


    def download_directory(
        self,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        """
        Download a directory from an local repo using its .dir metadata object.

        Args:
            current_directory (str): The current working directory .
            object_name (str): Key (path) of the .dir object in the local repository.
            download_loc (str): Local directory path where the directory should be downloaded.

        Returns:
            tuple: (total_files_in_directory, files_downloaded, status) where status indicates success (True) or failure (False).
        """

        # get_file() only creates file, to put artifacts in proper directory, subfolders are required.
        # download_loc = contains absolute path of the file with file name and extension
        dir_path = ""
        if "/" in download_loc:
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            os.makedirs(dir_path, mode=0o777, exist_ok=True)  # creating subfolders if needed

        """"
        if object_name ends with .dir - it is a directory.
        we download .dir object with 'temp_dir' and remove 
        this after all the files from this .dir object is downloaded.
        """
        # in case of .dir, download_loc is a absolute path for a folder
        os.makedirs(download_loc, mode=0o777, exist_ok=True)
        total_files_in_directory = 0
        files_downloaded = 0

        # Temporary file to download the .dir metadata object.
        temp_dir = f"{download_loc}/dir"
        try:
            # Download the .dir file containing metadata about tracked files.
            response = self.fs.get_file(object_name, temp_dir)
            
            with open(temp_dir, 'r') as file:
                tracked_files = eval(file.read())

            # removing temp_dir
            if os.path.exists(temp_dir):
                os.remove(temp_dir)

            """
            object_name = "files/md5/9b/9a458ac0b534f088a47c2b68bae479.dir" 
            contains the path of the .dir on the artifact repo
            we need to remove the hash of the .dir from the object_name
            which will leave us with the artifact repo path
            """
            repo_path = "/".join(object_name.split("/")[:-2])

            obj = True
            for file_info in tracked_files:
                total_files_in_directory += 1
                relpath = file_info['relpath']
                md5_val = file_info['md5']
                # md5_val = a237457aa730c396e5acdbc5a64c8453
                # we need a2/37457aa730c396e5acdbc5a64c8453
                formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                temp_object_name = f"{repo_path}/{formatted_md5}"
                temp_download_loc = f"{download_loc}/{relpath}"
                try:
                    obj = self.fs.get_file(temp_object_name, temp_download_loc)
                    if obj == None: 
                        files_downloaded += 1
                        print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
                    else:
                        print(f"object {temp_object_name} is not downloaded.")
                # this exception is for get_file() function for temp_object_name
                except Exception as e:
                    print(f"object {temp_object_name} is not downloaded.")

            # total_files - files_downloaded gives us the number of files which are failed to download
            if (total_files_in_directory - files_downloaded) == 0:   
                return total_files_in_directory, files_downloaded, True
            return total_files_in_directory, files_downloaded, False  
        # this exception is for get_file() function for object_name
        except Exception as e:
            print(f"object {object_name} is not downloaded.")
            # We usually don't count .dir as a file while counting total_files_in_directory.
            # However, here we failed to download the .dir folder itself. 
            # So we need to make, total_files_in_directory = 1
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False

        # sometimes we get TypeError as an execption, however investiagtion for the exact scenarios is pending
