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

import base64
import os
import logging
import paramiko

logger = logging.getLogger(__name__)

class SSHremoteArtifacts:

    def __init__(self, dvc_config_op):
        """
        Initialize the SSH artifact handler with credentials from the DVC config.

        Parameters
        ----------
        dvc_config_op : dict
            Dictionary produced by parsing the DVC config file.  Must contain:
              - "remote.ssh-storage.user"     : SSH login username
              - "remote.ssh-storage.password" : SSH login password

        Instance variables
        ------------------
        self.user     : SSH username used for every connection attempt.
        self.password : SSH password used for every connection attempt.
        self._ssh     : Active paramiko.SSHClient instance, or None if not connected.
        self._sftp    : Active paramiko.SFTPClient instance, or None if not connected.
        self._host    : Hostname/IP of the currently open connection, or None.
        """
        self.user = dvc_config_op["remote.ssh-storage.user"]
        self.password = dvc_config_op["remote.ssh-storage.password"]
        # Connection state variables initialized to None; populated on demand by _get_connection()
        self._ssh = None
        self._sftp = None
        self._host = None

    def _get_connection(self, host: str):
        """
        Return an active SFTPClient for the given host, reusing the existing
        connection when possible to avoid repeated SSH handshakes.

        A new connection is opened only when:
          - No connection has been established yet, or
          - The existing SSH transport has dropped / become inactive, or
          - The requested host differs from the currently connected host.

        Parameters
        ----------
        host : str
            Hostname or IP address of the SSH server to connect to.

        Returns
        -------
        paramiko.SFTPClient
            An open SFTP client ready for file transfers.
        """
        # Check whether the current SSH session is still alive
        transport_active = (
            self._ssh is not None
            and self._ssh.get_transport() is not None
            and self._ssh.get_transport().is_active()
        )
        if not transport_active or self._host != host:
            # Tear down any stale connection before opening a fresh one
            self._close_connection()
            ssh = paramiko.SSHClient()
            # Automatically accept unknown host keys.
            # Note: In high-security environments consider loading known_hosts
            # explicitly instead of using AutoAddPolicy.
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=self.user, password=self.password)
            self._ssh = ssh
            # Open an SFTP subsystem on top of the SSH connection
            self._sftp = ssh.open_sftp()
            self._host = host
        return self._sftp

    def _close_connection(self):
        """
        Safely close the SFTP channel and the underlying SSH transport.

        Both close calls are wrapped in try/except so that already-dead sockets
        or other cleanup errors do not propagate.  After this method returns,
        _sftp, _ssh, and _host are all reset to None.
        """
        try:
            if self._sftp:
                self._sftp.close()
        except Exception:
            pass
        try:
            if self._ssh:
                self._ssh.close()
        except Exception:
            pass
        self._sftp = None
        self._ssh = None
        self._host = None
        
    def __del__(self):
        """Called automatically by Python when this object is destroyed.
        Ensures SSH/SFTP connection is always closed even if close() is never called explicitly.
        e.g. when sshremote_class_obj goes out of scope in pull.py after return/raise.
        """
        self._close_connection()

    def download_file(
        self,
        host: str,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        """
        Download a single artifact file from the remote SSH storage via SFTP.

        Parameters
        ----------
        host : str
            Hostname or IP address of the SSH server
            e.g. "192.168.1.10" or "my-ssh-server.example.com"
        current_directory : str
            The local working directory used to resolve relative download paths.
            e.g. "/home/user/project"
        object_name : str
            Full absolute path to the file on the remote SSH server.
            e.g. "/home/user/ssh-storage/files/md5/23/6d9502e0283d91f689d7038b8508a2"
        download_loc : str
            Destination path for the downloaded file (may be absolute or relative).
            e.g. "artifacts/model/model.pkl"  or  "/home/user/artifacts/model/model.pkl"

        Returns
        -------
        tuple(str, str, bool)
            (object_name, abs_download_loc, success)
            - object_name     : remote path that was attempted (same as input)
            - abs_download_loc: absolute local path where the file was saved
            - success         : True  if the file was downloaded and its size
                                      matches the remote file size
                                False if the download failed or sizes differ
        """
        dir_path = ""
        # If download_loc is an absolute path (e.g. /home/user/artifacts/model.pkl),
        # strip the leading '/' so it can be safely joined with current_directory
        # using os.path.join without discarding current_directory.
        if os.path.isabs(download_loc):
            download_loc = download_loc[1:]
        if "/" in download_loc:
            # Extract only the directory portion of the path, ignoring the filename.
            # e.g. "artifacts/model/model.pkl" -> dir_path = "artifacts/model"
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            # Recursively create all intermediate directories so the file can
            # be written to the correct location.
            os.makedirs(dir_path, mode=0o777, exist_ok=True)

        # Build the absolute path where the file will be saved locally.
        # e.g. current_directory="/home/user/project", download_loc="artifacts/model/model.pkl"
        #   -> abs_download_loc = "/home/user/project/artifacts/model/model.pkl"
        abs_download_loc = os.path.abspath(os.path.join(current_directory, download_loc))
        try:
            sftp = self._get_connection(host)
            # Fetch remote file size before downloading; used later for integrity check.
            remote_file_size = sftp.stat(object_name).st_size
            # Transfer the remote file to the local absolute path.
            sftp.get(object_name, abs_download_loc)
            # Integrity check: verify that the downloaded file is complete by comparing
            # its size with the size reported by the remote server.
            local_file_size = os.stat(abs_download_loc).st_size
            if local_file_size == remote_file_size:
                return object_name, abs_download_loc, True   # Download successful
            return object_name, abs_download_loc, False      # Size mismatch — incomplete download
        except Exception as e:
            logger.error(f"object {object_name} is not downloaded. Error: {e}")
            return object_name, abs_download_loc, False

    def download_directory(
        self,
        host: str,
        current_directory: str,
        object_name: str,
        download_loc: str,
    ):
        """
        Download an artifact directory with its files from the remote SSH storage via SFTP.

        DVC represents tracked directories as a special `.dir` metadata file.
        That file contains a JSON list of entries, each with:
          - "relpath" : relative path of the file within the directory
          - "md5"     : md5 hash of that file, used to locate it in the content-
                        addressable store under <repo>/files/md5/<xx>/<rest>

        This method:
          1. Downloads the `.dir` with its files to a temporary location.
          2. Parses the `.dir` file to discover all member files.
          3. Downloads each member file into the correct sub-path.
          4. Returns counts of total vs successfully downloaded files.

        Parameters
        ----------
        host : str
            Hostname or IP address of the SSH server.
            e.g. "192.168.1.10"
        current_directory : str
            Local working directory used to resolve relative paths.
            e.g. "/home/user/project"
        object_name : str
            Full absolute path to the `.dir` file on the remote server.
            e.g. "/home/user/ssh-storage/files/md5/dd/2d792b7cf6efb02231f85c6147e403.dir"
        download_loc : str
            Local destination directory for all extracted files (may be absolute or relative).
            e.g. "artifacts/raw_data"

        Returns
        -------
        tuple(int, int, bool)
            (total_files_in_directory, files_downloaded, success)
            - total_files_in_directory : number of files listed in the .dir file
            - files_downloaded         : number of files successfully transferred
            - success                  : True  if every file was downloaded successfully
                                         False if one or more files failed, or if the
                                               .dir file itself could not be fetched
                                               (in which case total_files_in_directory=1)
        """
        dir_path = ""
        # Strip leading '/' from absolute paths so os.path.join works correctly
        # when building paths relative to current_directory.
        if os.path.isabs(download_loc):
            download_loc = download_loc[1:]
        if "/" in download_loc:
            # Extract only the directory portion, ignoring the base name.
            # e.g. "artifacts/raw_data" -> dir_path = "artifacts"
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            # Create all intermediate parent directories for the destination.
            os.makedirs(dir_path, mode=0o777, exist_ok=True)

        # Absolute local path to the destination directory that will hold all
        # files extracted from this .dir artifact.
        abs_download_loc = os.path.abspath(os.path.join(current_directory, download_loc))

        # Create the destination directory itself (the .dir artifact represents
        # a folder, so the local target must also be a folder).
        os.makedirs(abs_download_loc, mode=0o777, exist_ok=True)

        # Temporary path used to hold the downloaded .dir file before
        # it is parsed. It is removed immediately after reading.
        temp_dir = f"{abs_download_loc}/temp_dir"
        files_downloaded = 0
        total_files_in_directory = 0
        try:
            sftp = self._get_connection(host)

            # Step 1: Download the .dir with its file from the remote server.
            # The file is a JSON list like:
            #   [{"md5": "a237457aa730c396e5acdbc5a64c8453", "relpath": "train.csv"}, ...]
            sftp.get(object_name, temp_dir)
            with open(temp_dir, 'r') as file:
                tracked_files = eval(file.read())  # Parse the JSON list

            # Step 2: Clean up the temporary .dir file — it is no longer needed.
            if os.path.exists(temp_dir):
                os.remove(temp_dir)

            # Step 3: Derive the base repository path by stripping the last two
            # path segments (the "<xx>/<hash>.dir" part) from object_name.
            #
            # Example:
            #   object_name = "/home/user/ssh-storage/files/md5/dd/2d792b7cf6efb02231f85c6147e403.dir"
            #   Split by "/"  -> [..., "files", "md5", "dd", "2d792...403.dir"]
            #   Drop last 2   -> [..., "files", "md5"]
            #   repo_path     = "/home/user/ssh-storage/files/md5"
            repo_path = "/".join(object_name.split("/")[:-2])

            # Step 4: Iterate over every file recorded in the .dir file and
            # download each one individually.
            for file_info in tracked_files:
                total_files_in_directory += 1
                relpath = file_info['relpath']   # Relative path within the artifact directory
                md5_val = file_info['md5']       # MD5 hash used to locate the file in the store

                # DVC stores content-addressed files using the first 2 hex characters
                # of the hash as a subdirectory.
                # e.g. md5_val = "a237457aa730c396e5acdbc5a64c8453"
                #      formatted_md5 = "a2/37457aa730c396e5acdbc5a64c8453"
                formatted_md5 = md5_val[:2] + '/' + md5_val[2:]

                # Local path where this individual file will be saved.
                # e.g. /home/user/project/artifacts/raw_data/train.csv
                temp_download_loc = f"{abs_download_loc}/{relpath}"

                # Remote path to the actual file content on the SSH server.
                # e.g. /home/user/ssh-storage/files/md5/a2/37457aa730c396e5acdbc5a64c8453
                temp_object_name = f"{repo_path}/{formatted_md5}"

                try:
                    remote_file_size = sftp.stat(temp_object_name).st_size
                    sftp.get(temp_object_name, temp_download_loc)
                    # Integrity check: confirm the downloaded file size matches the remote size.
                    if os.stat(temp_download_loc).st_size == remote_file_size:
                        files_downloaded += 1
                        logger.info(f"object {temp_object_name} downloaded at {temp_download_loc}.")
                    else:
                        logger.error(f"object {temp_object_name} is not fully downloaded: size mismatch.")
                except Exception as e:
                    logger.error(f"object {temp_object_name} is not downloaded. Error: {e}")

            # Return success only when every file in the .dir file was downloaded.
            if (total_files_in_directory - files_downloaded) == 0:
                return total_files_in_directory, files_downloaded, True
            return total_files_in_directory, files_downloaded, False

        except Exception as e:
            # Catches fatal errors during directory download.
            logger.error(f"object {object_name} is not downloaded. Error: {e}")
            # We usually don't count .dir as a file while counting total_files_in_directory.
            # However, here we failed to download the .dir folder itself. 
            # So we need to make, total_files_in_directory = 1
            total_files_in_directory = 1
            return total_files_in_directory, files_downloaded, False
