import os
import paramiko



class sshremote_artifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        host: str,
        current_directory: str,
        current_loc: str,
        download_loc: str,
    ):
        obj = True
        remote_repo = dvc_config_op[1]
        user = dvc_config_op[2]
        password = dvc_config_op[4]
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # this can lead to man in the middle attack, need to find another solution
            ssh.connect(host, username=user, password=password)
            sftp = ssh.open_sftp()
            #temp = download_loc.split("/")
            #temp.pop()
            #dir_path = "/".join(temp)
            #dir_to_create = os.path.join(current_directory, dir_path)
            #os.makedirs(dir_to_create, mode=0o777, exist_ok=True)
            
            download_file_path = os.path.join(current_directory, download_loc)
            sftp.put(current_loc, download_file_path)
            sftp.close()
            ssh.close()
            # fs = DVCFileSystem(remote_repo)
            # temp = download_loc.split("/")
            # temp.pop()
            # dir_path = "/".join(temp)
            # dir_to_create = os.path.join(current_directory, dir_path)
            # os.makedirs(dir_to_create, mode=0o777, exist_ok=True)
            # obj = fs.get_file(current_dvc_loc, download_loc)

            if obj == None:
                stmt = f"object {current_loc} downloaded at {download_loc}."
                return stmt

        except TypeError as exception:
            return exception
        except Exception as exception:
            return exception
