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
    def download_artifacts(
        self,
        dvc_config_op,
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
    ):
        access_key = dvc_config_op["remote.amazons3.access_key_id"]
        secret_key = dvc_config_op["remote.amazons3.secret_access_key"]
        session_token = dvc_config_op["remote.amazons3.session_token"]
        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
            s3.head_bucket(Bucket=bucket_name)

            dir_path = ""
            if "/" in download_loc:
                dir_path, _ = download_loc.rsplit("/", 1)
            if dir_path != "":
                os.makedirs(dir_path, mode=0o777, exist_ok=True)  # creating subfolders if needed

            response = ""

            """"
            if object_name ends with .dir - it is a directory.
            we download .dir object with 'temp_dir' and remove 
            this after all the files from this .dir object is downloaded.
            """
            if object_name.endswith('.dir'):
                # in case of .dir, download_loc is a absolute path for a folder
                os.makedirs(download_loc, mode=0o777, exist_ok=True)

                # download .dir object
                temp_dir = f"{download_loc}/temp_dir"
                response = s3.download_file(bucket_name, object_name, temp_dir)

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
                for file_info in tracked_files:
                    relpath = file_info['relpath']
                    md5_val = file_info['md5']
                    # download_loc =  /home/user/datatslice/example-get-started/test/artifacts/raw_data
                    # md5_val = a237457aa730c396e5acdbc5a64c8453
                    # we need a2/37457aa730c396e5acdbc5a64c8453
                    formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                    temp_download_loc = f"{download_loc}/{relpath}"
                    temp_object_name = f"{repo_path}/{formatted_md5}"
                    obj = s3.download_file(bucket_name, temp_object_name, temp_download_loc)
                    if obj == None:
                        print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
            else:
                # download objects which are file
                response = s3.download_file(bucket_name, object_name, download_loc)
            if response == None:
                return f"{object_name} downloaded at {download_loc}"
            return response

        except s3.exceptions.ClientError as e:
            # If a specific error code is returned, the bucket does not exist
            if e.response['Error']['Code'] == '404':
                return f"{bucket_name}  doesn't exists!!"
            else:
                # Handle other errors
               raise
        except TypeError as exception:
            return exception
        except Exception as e:
            return e
