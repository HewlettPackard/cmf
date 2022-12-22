import subprocess
import os


def fix_subparsers(subparsers):
    subparsers.required = True
    subparsers.dest = "cmd"


def create_cmf_config(file_name: str, cmf_server_ip: str):
    with open(file_name, "w") as file:
         file.write(f"cmf.server.ip={cmf_server_ip}")

def read_cmf_config(file_name: str):
    with open(file_name, "r") as file:
         return file.read()

def git_exists():
    try:
        output = subprocess.check_output(["git", "version"]).decode("ascii")
        return output
    except FileNotFoundError:
        return "\033[1;31mERROR:\033[1;m git is not installed!! Install git."

def find_root(file_name: str):

    msg = "'cmf' is not configured.\nExecute 'cmf init' command."
    root_dir = os.path.realpath(os.getcwd())
    while True:
        file_path = os.path.join(root_dir, file_name)
        if os.path.exists(file_path):
            return root_dir
        if os.path.ismount(root_dir):
            return msg
        parent = os.path.abspath(os.path.join(root_dir, os.pardir))
        if parent == root_dir:
            return msg
        root_dir = parent


def check_minio_server():
    from minio import Minio
    from minio.error import S3Error
    from cmflib.dvc_config import dvc_config

    dvc_config_op = dvc_config.get_dvc_config()  # pulling dvc config
    if dvc_config_op[0] == "minio":
        endpoint = dvc_config_op[1].split("http://")[1]  # endpoint url from config
        access_key = dvc_config_op[2]  # access key from dvc config
        secret_key = dvc_config_op[3]  # secret key from dvc config
        bucket_name = dvc_config_op[4].split("s3://")[1]  # url from dvc config
        try:
            client = Minio(
                endpoint, access_key=access_key, secret_key=secret_key, secure=False
            )
            found = client.bucket_exists(bucket_name)
            if found:
                return "SUCCESS"
        except TypeError as exception:
            return exception
        except S3Error as exception:
            return exception


def main():
    # create_cmf_config("./.cmfconfig", "http://127.0.0.1:80")
    print(find_root(".cmfconfig"))


if __name__ == "__main__":
    main()
