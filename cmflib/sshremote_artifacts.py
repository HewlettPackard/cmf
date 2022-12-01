import os
import paramiko

class sshremote_artifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        host: str,
        current_directory: str,
        remote_file_path: str,
        local_path: str,
    ):
        output = ""
        remote_repo = dvc_config_op[1]
        user = dvc_config_op[2]
        password = dvc_config_op[4]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # this can lead to man in the middle attack, need to find another solution
            ssh.connect(host, username=user, password=password)
            sftp = ssh.open_sftp()
            temp = local_path.split("/")
            temp.pop()
            dir_path = "/".join(temp)
            dir_to_create = os.path.join(current_directory, dir_path)
            os.makedirs(dir_to_create, mode=0o777, exist_ok=True)
            local_file_path = os.path.join(current_directory, local_path)
            output = sftp.put(remote_file_path, local_file_path)
            sftp.close()
            ssh.close()
            if output:
                stmt = f"object {remote_file_path} downloaded at {local_file_path}."
                return stmt

        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
