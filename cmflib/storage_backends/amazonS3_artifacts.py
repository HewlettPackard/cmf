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


class AmazonS3Artifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
    ):
        access_key = dvc_config_op[
            "remote.amazons3.access_key_id"
        ]  # pulling access_key from dvc config output
        secret_key = dvc_config_op[
            "remote.amazons3.secret_access_key"
        ]  # pulling secret_key from dvc config output
        try:
            client = Minio(
                "s3.amazonaws.com", access_key=access_key, secret_key=secret_key
            )
            found = client.bucket_exists(bucket_name)
            if not found:
                return "Bucket doesn't exists"

            obj = client.fget_object(bucket_name, object_name, download_loc)
            if obj:
                stmt = f"object {object_name} downloaded at {download_loc}."
                return stmt
            else:
                return f"object {object_name} is not downloaded."

        except TypeError as exception:
            return exception
        except S3Error as exception:
            return exception
