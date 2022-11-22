import os
from minio import Minio
from minio.error import S3Error
from .dvc_config import dvc_config


class amazonS3_artifacts:
    def download_artifacts(
        self, current_directory: str, bucket_name: str, object_name: str, file_path: str
    ):
        endpoint = "s3.amazonaws.com"
        access_key = ""
        secret_key = ""
        try:
            bucket_name, access_key, secret_key = dvc_config.get_dvc_config()
            print(bucket_name, access_key, secret_key)
            client = Minio(endpoint, access_key=access_key, secret_key=secret_key)
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
            return exception
        except S3Error as exception:
            return exception
