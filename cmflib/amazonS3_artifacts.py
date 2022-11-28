import os
from minio import Minio
from minio.error import S3Error
from .dvc_config import dvc_config


class amazonS3_artifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        current_directory: str,
        bucket_name: str,
        object_name: str,
        download_loc: str,
    ):
        access_key = dvc_config_op[2]
        secret_key = dvc_config_op[3]
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
