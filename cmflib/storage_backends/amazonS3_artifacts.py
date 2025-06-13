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
import boto3

class AmazonS3Artifacts:

    def __init__(self, dvc_config_op):
        """
        Initialize the AmazonS3Artifacts class with AWS credentials.

        Args:
            dvc_config_op (dict): Dictionary containing AWS credentials (access key, secret key, and session token).
        """
        self.access_key = dvc_config_op["remote.amazons3.access_key_id"]
        self.secret_key = dvc_config_op["remote.amazons3.secret_access_key"]
        self.session_token = dvc_config_op["remote.amazons3.session_token"]

        # Create an S3 client with the provided credentials.
        self.s3 = boto3.client(
                's3',
                aws_access_key_id = self.access_key,
                aws_secret_access_key = self.secret_key,
                aws_session_token = self.session_token
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
            bucket_name (str): Name of the s3 bucket.
            object_name (str): Key (path) of the file in the s3 bucket.
            download_loc (str): Local path where the file should be downloaded.

        Returns:
            tuple: (object_name, download_loc, status) where status indicates success (True) or failure (False).
        """
        try:
            response = ""

            # Check if the bucket exists.
            self.s3.head_bucket(Bucket=bucket_name)
            
            # Create necessary directories for the download location.
            dir_path = ""
            if "/" in download_loc:
                dir_path, _ = download_loc.rsplit("/", 1)
            if dir_path != "":
                os.makedirs(dir_path, mode=0o777, exist_ok=True)  # creating subfolders if needed
            
            # Download the file
            response = self.s3.download_file(bucket_name, object_name, download_loc)
            
            # Check if the response indicates success.
            if response == None:
                return object_name, download_loc, True
            else:
                return object_name, download_loc, False
        except self.s3.exceptions.ClientError as e:
            # If a specific error code is returned, the bucket does not exist
            if e.response['Error']['Code'] == '404':
                print(f"{bucket_name}  doesn't exists!!")
                return object_name, download_loc, False   
            else:
                print(e)
                return object_name, download_loc, False
        except Exception as e:
            return object_name, download_loc, False

    def download_directory(self,
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
    ):
        """
        Download a directory from an S3 bucket using its .dir metadata object.

        Args:
            current_directory (str): The current working directory .
            bucket_name (str): Name of the S3 bucket.
            object_name (str): Key (path) of the .dir object in the S3 bucket.
            download_loc (str): Local directory path where the directory should be downloaded.

        Returns:
            tuple: (total_files_in_directory, files_downloaded, status) where status indicates success (True) or failure (False).
        """
        
        self.s3.head_bucket(Bucket=bucket_name)
        """"
        if object_name ends with .dir - it is a directory.
        we download .dir object with 'temp_dir' and remove 
        this after all the files from this .dir object is downloaded.
        """
        # in case of .dir, download_loc is a absolute path for a folder
        dir_path = ""
        if "/" in download_loc:
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            os.makedirs(dir_path, mode=0o777, exist_ok=True)  # creating subfolders if needed
        os.makedirs(download_loc, mode=0o777, exist_ok=True)
        total_files_in_directory = 0
        files_downloaded = 0

        # Temporary file to download the .dir metadata object.
        temp_dir = f"{download_loc}/temp_dir"
        try:
            # Download the .dir file containing metadata about tracked files.
            response = self.s3.download_file(bucket_name, object_name, temp_dir)
            
            # Read the .dir metadata to get file information.
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
            repo_path = "/".join(object_name.split("/")[:-2])
            obj=True
            for file_info in tracked_files:
                total_files_in_directory += 1
                relpath = file_info['relpath']
                md5_val = file_info['md5']
                # download_loc =  /home/user/datatslice/example-get-started/test/artifacts/raw_data
                # md5_val = a237457aa730c396e5acdbc5a64c8453
                # we need a2/37457aa730c396e5acdbc5a64c8453
                formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                temp_download_loc = f"{download_loc}/{relpath}"
                temp_object_name = f"{repo_path}/{formatted_md5}"
                
                obj = self.s3.download_file(bucket_name, temp_object_name, temp_download_loc)
                if obj == None:
                    files_downloaded += 1
                    print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
                else:
                    print(f"object {temp_object_name} is not downloaded.")

            # Check if all files were successfully downloaded.
            if (total_files_in_directory - files_downloaded) == 0:   
                return total_files_in_directory, files_downloaded, True
            return total_files_in_directory, files_downloaded, False   
        except self.s3.exceptions.ClientError as e:
            # If a specific error code is returned, the bucket does not exist
            if e.response['Error']['Code'] == '404':
                print(f"{bucket_name}  doesn't exists!!")
                total_files_in_directory = 1 
                return total_files_in_directory, files_downloaded, False    
            print(e)
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False
        except Exception as e:
            print(f"object {object_name} is not downloaded.")
            # Handle failure to download the .dir metadata.
            # need to improve this  
            # We usually don't count .dir as a file while counting total_files_in_directory.
            # However, here we failed to download the .dir folder itself. So we need to make 
            # total_files_in_directory = 1, because  ..............
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False

        
            