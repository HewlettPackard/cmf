import subprocess
import os
import sys

def fix_subparsers(subparsers):
    subparsers.required = True
    subparsers.dest = "cmd"


def create_cmf_config(file_name: str, cmf_server_ip: str):
    try:
        with open(file_name, "w") as file:
            file.write(f"cmf.server.ip={cmf_server_ip}")
    except IOError as e:
        print("I/O error",e) 
        sys.exit()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        sys.exit()


def read_cmf_config(file_name: str):
    try:
        with open(file_name, "r") as file:
            return file.read()
    except IOError as e:
        print("I/O error", e)
    except:
        print("Unexpected error:", sys.exc_info()[0])

def git_exists():
    try:
        output = subprocess.check_output(["git", "version"]).decode("ascii")
        return output
    except FileNotFoundError:
        return "ERROR: git is not installed!! Install git."


def find_root(file_name: str):
    """This function returns the root of the file passed as a parameter.
    It searches for the file in the parent directory until the mount
    if it is not in the current directory.
    """
    msg = "'cmf' is not configured.\nExecute 'cmf init' command."
    # make current directory as root directory
    root_dir = os.path.realpath(os.getcwd())
    while True:
        # adding file name to the root directory
        file_path = os.path.join(root_dir, file_name)
        # whether file path exists, if yes return function with root_dir
        if os.path.exists(file_path):
            return root_dir
        # as file doesn't exists in root_dir and if root_dir is mount directory return msg
        if os.path.ismount(root_dir):
            return msg
        # assigning parent of root_dir
        parent = os.path.abspath(os.path.join(root_dir, os.pardir))
        # if value of parent become root_dir, this condition
        # if parent == root_dir:
        #    return msg
        root_dir = parent


def check_minio_server(dvc_config_op):
    from minio import Minio
    from minio.error import S3Error

    if dvc_config_op["core.remote"] == "minio":
        print(dvc_config_op["core.remote"])
        endpoint = dvc_config_op["remote.minio.endpointurl"].split("http://")[1]  # endpoint url from config
        access_key = dvc_config_op["remote.minio.access_key_id"]  # access key from dvc config
        secret_key = dvc_config_op["remote.minio.secret_access_key"]  # secret key from dvc config
        bucket_name = dvc_config_op["remote.minio.url"].split("s3://")[1]  # url from dvc config
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
    # print(find_root(".cmfconfig"))
    config = { "core.remote": "minio",
               "remote.minio.endpointurl": "http://127.0.0.1:80"
    }
    print(check_minio_server(config))


if __name__ == "__main__":
    main()
