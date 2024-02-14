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
