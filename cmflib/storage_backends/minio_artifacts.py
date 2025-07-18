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
import typing as t
from minio import Minio
from minio.error import S3Error
from cmflib.cmf_exception_handling import BucketNotFound

class MinioArtifacts:

    def __init__(self, dvc_config_op):
        """
        Initialize the MinioArtifacts class with minios3 repo credentials.
        dvc_config_op["remote.minio.endpointurl"] = http://XX.XX.XX.XX:9000
        Args:
            dvc_config_op (dict): Dictionary containing local url (remote.local.url).
        """
        
        self.endpoint = dvc_config_op["remote.minio.endpointurl"].split("http://")[1]
        self.access_key = dvc_config_op["remote.minio.access_key_id"]
        self.secret_key = dvc_config_op["remote.minio.secret_access_key"]
        self.client = Minio(
                self.endpoint, access_key=self.access_key, secret_key=self.secret_key, secure=False
            )


    def download_file(
        self, 
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
        ):
        """
        Download a single file from an S3 bucket.

        Args:
            current_directory (str): The current working directory.
            bucket_name (str): Name of the minioS3 bucket.
            object_name (str): Key (path) of the file in the minios3 repo.
            download_loc (str): Local path where the file should be downloaded.

        Returns:
            tuple: (object_name, download_loc, status) where status indicates success (True) or failure (False).
        """
        try:
            found = self.client.bucket_exists(bucket_name)

            #check if minio bucket exists
            if not found:   
                raise BucketNotFound(bucket_name)

            #Download file
            response = self.client.fget_object(bucket_name, object_name, download_loc)

            # Check if the response indicates success.
            if response:
                return object_name, download_loc, True
            return object_name, download_loc, False
        except S3Error as exception:
            print(exception)
            return object_name, download_loc, False
        except Exception as e:
            return object_name, download_loc, False


    def download_directory(
        self,
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
    ):
        """
        Download a directory from an minios3 repo using its .dir metadata object.

        Args:
            current_directory (str): The current working directory .
            bucket_name (str): Name of the minios3 bucket.
            object_name (str): Key (path) of the .dir object in the minios3 bucket.
            download_loc (str): Local directory path where the directory should be downloaded.

        Returns:
            tuple: (total_files_in_directory, files_downloaded, status) where status indicates success (True) or failure (False).
        """

        found = self.client.bucket_exists(bucket_name)
        if not found:   #check if minio bucket exists
            raise BucketNotFound(bucket_name)

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
        temp_dir = f"{download_loc}/temp_dir"
        try:
            # Download the .dir file containing metadata about tracked files.
            response = self.client.fget_object(bucket_name, object_name, temp_dir)

            with open(temp_dir, 'r') as file:
                tracked_files = eval(file.read())

            # removing temp_dir
            if os.path.exists(temp_dir):
                os.remove(temp_dir)

            """
            object_name =  files/md5/c9/d8fdacc0d942cf8d7d95b6301cfb97.dir
            contains the path of the .dir on the artifact repo
            we need to remove the hash of the .dir from the object_name
            which will leave us with the artifact repo path
            """
            repo_path_list: t.List[str] = object_name.split("/")
            repo_path_list = repo_path_list[:len(repo_path_list)-2]
            repo_path = "/".join(repo_path_list)

            obj=True
            for file_info in tracked_files:
                total_files_in_directory += 1
                relpath = file_info['relpath']
                md5_val = file_info['md5']
                # download_loc =  /home/sharvark/datatslice/example-get-started/test/artifacts/raw_data
                # md5_val = a237457aa730c396e5acdbc5a64c8453
                # we need a2/37457aa730c396e5acdbc5a64c8453
                formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                temp_download_loc = f"{download_loc}/{relpath}"
                temp_object_name = f"{repo_path}/{formatted_md5}"
                try:
                    obj = self.client.fget_object(bucket_name, temp_object_name, temp_download_loc)
                    if obj:
                        files_downloaded +=1
                        print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
                    else:
                        print(f"object {temp_object_name} is not downloaded.")
                except Exception as e:
                    print(f"object {temp_object_name} is not downloaded.")
                    
            # total_files - files_downloaded gives us the number of files which are failed to download
            if (total_files_in_directory - files_downloaded) == 0:   
                return total_files_in_directory, files_downloaded, True
            return total_files_in_directory, files_downloaded, False  
        except S3Error as exception:
            print(exception)
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False
        except Exception as e:
            print(f"object {object_name} is not downloaded.")
            # need to improve this  
            # We usually don't count .dir as a file while counting total_files_in_directory.
            # However, here we failed to download the .dir folder itself. So we need to make 
            # total_files_in_directory = 1, because  ..............
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False
    
        # sometimes we get TypeError as an execption, however investiagtion for the exact scenarios is pending
