import os
from minio import Minio
from minio.error import S3Error
from .dvc_config import dvc_config

class minio_artifacts:
    #    def get_dvc_config(self, current_directory: str):
    #       dvc_path = current_directory + "/.dvc/config"
    #      if os.path.exists(dvc_path):
    #         file = open(dvc_path, "r")
    #       while True:
    #            line = file.readline()
    #                if not line:
    #                   break
    #              if line.find("endpointurl") != -1:
    #                 temp = line.split()[2]
    #                endpoint = ''.join(temp.split("http://", 1))
    #           elif line.find("access_key_id") != -1:
    #              access_key = line.split()[2]
    #         elif line.find("secret_access_key") != -1:
    #            secret_key = line.split()[2]
    #   return endpoint, access_key, secret_key
    #  else:
    #     pass

    def download_artifacts(
        self, current_directory: str, bucket_name: str, object_name: str, file_path: str
    ):
        endpoint = ""
        access_key = ""
        secret_key = ""
        try:
            endpoint, access_key, secret_key = dvc_config.get_dvc_config()
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
