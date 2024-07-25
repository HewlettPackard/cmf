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
from minio import Minio
from minio.error import S3Error


class MinioArtifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
    ):
        endpoint = dvc_config_op["remote.minio.endpointurl"].split("http://")[1]
        access_key = dvc_config_op["remote.minio.access_key_id"]
        secret_key = dvc_config_op["remote.minio.secret_access_key"]
        try:
            client = Minio(
                endpoint, access_key=access_key, secret_key=secret_key, secure=False
            )
            found = client.bucket_exists(bucket_name)
            if not found:
                return "Bucket doesn't exists"

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
                response = client.fget_object(bucket_name, object_name, temp_dir)

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
                repo_path = object_name.split("/")
                repo_path = repo_path[:len(repo_path)-2]
                repo_path = "/".join(repo_path)
                for file_info in tracked_files:
                    relpath = file_info['relpath']
                    md5_val = file_info['md5']
                    # download_loc =  /home/sharvark/datatslice/example-get-started/test/artifacts/raw_data
                    # md5_val = a237457aa730c396e5acdbc5a64c8453
                    # we need a2/37457aa730c396e5acdbc5a64c8453
                    formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                    temp_download_loc = f"{download_loc}/{relpath}"
                    temp_object_name = f"{repo_path}/{formatted_md5}"
                    obj = client.fget_object(bucket_name, temp_object_name, temp_download_loc)
                    if obj:
                        print(f"object {temp_object_name} downloaded at {temp_download_loc}.")
                    else:
                        print(f"object {temp_object_name} is not downloaded.")
            else:
                response = client.fget_object(bucket_name, object_name, download_loc)
            if response:
                stmt = f"object {object_name} downloaded at {download_loc}."
                return stmt
            else:
                return f"object {object_name} is not downloaded."

        except TypeError as exception:
            return exception
        except S3Error as exception:
            return exception
