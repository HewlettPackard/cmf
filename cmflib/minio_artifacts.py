import os
from minio import Minio
from minio.error import S3Error
from .dvc_config import dvc_config

class minio_artifacts:
    def download_artifacts(
        self, dvc_config_op, current_directory: str, bucket_name: str, object_name: str, file_path: str
    ):
        endpoint = dvc_config_op[1]
        access_key = dvc_config_op[2]
        secret_key = dvc_config_op[3]
        try:
            client = Minio(
                endpoint, access_key=access_key, secret_key=secret_key, secure=False
            )
            found = client.bucket_exists(bucket_name)
            if not found:
                return "Bucket doesn't exists"

            obj = client.fget_object(bucket_name, object_name, file_path)
            if obj:
                stmt = f"object {object_name} downloaded at {file_path}."
                return stmt
            else:
                return f"object {object_name} is not downloaded."

        except TypeError as exception:
            return f"Check if 'config' file present in .dvc/config. {exception}"
        except S3Error as exception:
            return exception
