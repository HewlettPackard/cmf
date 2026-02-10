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
import logging
import requests
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import hashlib
import time
import ast
from pathlib import Path

from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def generate_cached_url(url, cache):
    #This takes host URL as supplied from MLMD records and generates cached URL=cache_path + path
    #Example Input: https://sdsc-origin.nationalresearchplatform.org:8443/nrp/fdp/23/6d9502e0283d91f689d7038b8508a2
    #Example Output: https://osdf-director.osg-htc.org/nrp/fdp/23/6d9502e0283d91f689d7038b8508a2  
    #The assumption is that url obtained from MLMD is more accurate. So we use the path from this URL and append it to cache path
    #but we clean up the cache path to only its scheme + netloc: https://osdf-director.osg-htc.org
    parsed_url = urlparse(url)
    parsed_cache_url= urlparse(cache) 
    cached_url= parsed_cache_url.scheme + "://" + parsed_cache_url.netloc + parsed_url.path
    return cached_url 

def calculate_md5_from_file(file_path, chunk_size=8192):
    md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
    except Exception as e:
        logger.error(f"[calculate_md5_from_file] An error occurred while reading the file: {e}")
        return None
    return md5.hexdigest()

def download_and_verify_file(host, headers, remote_file_path, local_path, artifact_hash, timeout):
    """
    Download a file from the given host URL, write it to disk, and verify its MD5 hash.

    The function performs an HTTP GET request to ``host`` using the provided ``headers`` and
    ``timeout``. If data is received, it is written to ``remote_file_path``. The MD5 checksum of
    the downloaded file is then computed and compared against ``artifact_hash``.

    Args:
        host (str): Fully qualified URL from which to download the artifact.
        headers (dict): HTTP headers to include in the GET request.
        remote_file_path (str): Local filesystem path where the downloaded file will be written.
        local_path (str): Logical or original path/name used for logging and status messages.
        artifact_hash (str): Expected MD5 hash of the artifact, used for integrity verification.
        timeout (float | int): Timeout (in seconds) for the HTTP request.

    Returns:
        tuple[bool, str]: A pair ``(success, message)`` where ``success`` indicates whether the
            download and MD5 verification succeeded, and ``message`` describes the outcome.
    """
    #logger.info(f"Inside download_and_verify_file: Fetching artifact={local_path}, surl={host} to {remote_file_path}")
    data= None
    try:
        response = requests.get(host, headers=headers, timeout=timeout, verify=True)  # This should be made True. otherwise this will produce Insecure SSL Warning
        if response.status_code == 200 and response.content:
            data = response.content
        else:
            #logger.error(f"Inside download_and_verify_file: Failed to download file. HTTP Status Code: {response.status_code}. Response content: {response.content}")
            return False, "No data received from the server."
            #pass
    except requests.exceptions.Timeout:
        return False, "The request timed out."
        #pass
    except Exception as exception:
        #logger.error(f"Inside download_and_verify_file: An error occurred during the download: {exception}")
        return False, str(exception)

    if data is not None:
        try: 
            with open(remote_file_path, 'wb') as file:
                file.write(data)
            if os.path.exists(remote_file_path) and os.path.getsize(remote_file_path) > 0:
                # Calculate MD5 hash of the downloaded file
                start_time = time.time()
                md5_hash = calculate_md5_from_file(remote_file_path)
                end_time = time.time()
                time_taken = end_time - start_time
                if md5_hash:
                    #logger.debug(f"MD5 hash of the downloaded file is: {md5_hash}")
                    #logger.debug(f"Artifact hash from MLMD records is: {artifact_hash}")
                    #logger.debug(f"Time taken to calculate MD5 hash: {time_taken:.2f} seconds")
                    if artifact_hash == md5_hash:
                        #logger.debug("MD5 hash of the downloaded file matches the hash in MLMD records.")
                        stmt = f"object {local_path} downloaded at {remote_file_path} in {time_taken:.2f} seconds and matches MLMD records."
                        success=True
                    else:
                        #logger.error("Error: MD5 hash of the downloaded file does not match the hash in MLMD records.")
                        stmt = f"object {local_path} downloaded at {remote_file_path} in {time_taken:.2f} seconds and does NOT match MLMD records."
                        success=False
                    return success, stmt
                else:
                    logger.error("Failed to calculate MD5 hash of the downloaded file.")
        except Exception as e:
            return False, f"An error occurred while writing to the file: {e}"
    
    return False, "Data is None."


class OSDFremoteArtifacts:
    def __init__(self, dvc_config_op):
        """
        Initialize the OSDFremoteArtifacts class with OSDF configuration.

        Args:
            dvc_config_op (dict): Dictionary containing OSDF configuration including:
                - remote.osdf.url: Remote repository URL
                - remote.osdf.password: Dynamic password/token
                - remote.osdf.custom_auth_header: Custom authentication header name
        """
        self.remote_repo = dvc_config_op["remote.osdf.url"]
        self.user = "nobody"
        self.dynamic_password = dvc_config_op["remote.osdf.password"]
        self.custom_auth_header = dvc_config_op["remote.osdf.custom_auth_header"]
        self.headers = {self.custom_auth_header: self.dynamic_password}

    def _download_with_cache_fallback(
        self,
        host: str,
        cache: str,
        download_path: str,
        local_path: str,
        artifact_hash: str,
    ):
        """
        Helper method to download a file with cache fallback to origin.

        Args:
            host (str): Origin URL of the artifact.
            cache (str): Cache URL (can be empty).
            download_path (str): Absolute path where file will be saved.
            local_path (str): Local path for logging purposes.
            artifact_hash (str): MD5 hash for verification.

        Returns:
            tuple: (success, result_message)
        """
        #Cache can be Blank. If so, fetch from Origin
        if cache == "":
            #Fetch from Origin
            success, result = download_and_verify_file(host, self.headers, download_path, local_path, artifact_hash, timeout=10)
            if success:
                #logger.info(result)
                return success, result
            #logger.error(f"Failed to download and verify file: {result}")
            return success, result
        else:
            #Generate Cached path for artifact
            cached_s_url = generate_cached_url(host, cache)
            #Try to fetch from cache first
            success, cached_result = download_and_verify_file(cached_s_url, self.headers, download_path, local_path, artifact_hash, timeout=5)
            if success:
                #logger.info(cached_result)
                return success, cached_result
            else:
                logger.error(f"Failed to download and verify file from cache: {cached_result}")
                logger.info(f"Trying Origin at {host}")
                #Fetch from Origin 
                success, origin_result = download_and_verify_file(host, self.headers, download_path, local_path, artifact_hash, timeout=10)
                if success: 
                    #logger.info(origin_result)
                    return success, origin_result
                #logger.error(f"Failed to download and verify file: {origin_result}")
                return success, origin_result

    def download_file(
        self,
        host: str, # s_url
        cache: str, # cache_path from cmfconfig
        current_directory: str, # current_directory where cmf artifact pull is executed
        object_name: str, # name of the artifact
        download_loc: str, # download_loc of the artifact
        artifact_hash: str, # hash of the artifact from MLMD records
    ):
        """
        Download a single file from an OSDF repository.

        Args:
            host (str): Source URL of the artifact.
            cache (str): Cache path from cmfconfig (can be empty).
            current_directory (str): Current working directory where cmf artifact pull is executed.
            object_name (str): Key (path) of the file in the OSDF repo.
            download_loc (str): Local path where the file should be downloaded.
            artifact_hash (str): MD5 hash of the artifact from MLMD records.

        Returns:
            tuple: (object_name, download_loc, status) where status indicates success (True) or failure (False).
        """
        #logger.debug(f"Configured Host from MLMD record={host}. User configured cache redirector={cache}")
        #logger.debug(f"Fetching artifact={object_name}, surl={host} to {download_loc} when this has been called at {current_directory}")
        
        # Prepare directories and file paths
        dir_path = ""
        if "/" in download_loc:
            # extracts the directory path from download_loc
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            # creates subfolders needed as per artifacts' folder structure
            os.makedirs(dir_path, mode=0o777, exist_ok=True)
        
        # download_loc already contains the full path (from extract_repo_args), so use it directly
        abs_download_loc = os.path.abspath(download_loc)
        
        # Download with cache fallback to origin
        success, result = self._download_with_cache_fallback(
            host, cache, abs_download_loc, download_loc, artifact_hash
        )
        return object_name, abs_download_loc, success

    def download_directory(
        self,
        host: str, # s_url
        cache: str, # cache_path from cmfconfig
        current_directory: str, # current_directory where cmf artifact pull is executed
        object_name: str, # name of the artifact
        download_loc: str, # download_loc of the artifact
        artifact_hash: str, # hash of the artifact from MLMD records
    ):
        """
        Download a directory from an OSDF repo using its .dir metadata object.

        Args:
            host (str): Source URL of the artifact.
            cache (str): Cache path from cmfconfig (can be empty).
            current_directory (str): Current working directory.
            object_name (str): Key (path) of the .dir object in the OSDF repository.
            download_loc (str): Local directory path where the directory should be downloaded.
            artifact_hash (str): MD5 hash of the artifact from MLMD records.

        Returns:
            tuple: (total_files_in_directory, files_downloaded, status) where status indicates success (True) or failure (False).
        """
        #logger.debug(f"Configured Host from MLMD record={host}. User configured cache redirector={cache}")
        #logger.debug(f"Fetching artifact={object_name}, surl={host} to {download_loc} when this has been called at {current_directory}")
        # Prepare directories
        dir_path = ""
        if "/" in download_loc:
            # extracts the directory path from download_loc
            dir_path, _ = download_loc.rsplit("/", 1)
        if dir_path != "":
            # creates subfolders needed as per artifacts' folder structure
            os.makedirs(dir_path, mode=0o777, exist_ok=True)

        # download_loc already contains the full path (from extract_repo_args), so use it directly
        abs_download_loc = os.path.abspath(download_loc)
        #logger.debug(f"Absolute download location: {abs_download_loc}")
        
        # in case of .dir, abs_download_loc is an absolute path for a folder
        os.makedirs(abs_download_loc, mode=0o777, exist_ok=True)

        total_files_in_directory = 0
        files_downloaded = 0

        # download .dir object
        temp_dir = f"{abs_download_loc}/temp_dir"
        try:
            # Try to download from cache first if available, otherwise from origin
            success, result = self._download_with_cache_fallback(
                host, cache, temp_dir, temp_dir, artifact_hash
            )
            
            if not success:
                logger.error(f"object {object_name} is not downloaded.")
                total_files_in_directory = 1
                return total_files_in_directory, files_downloaded, False
            
            #logger.info(f"{object_name} downloaded at {download_loc} when this has been called at {current_directory}")

            # Parse .dir file safely using ast.literal_eval to prevent code execution vulnerabilities
            with open(temp_dir, 'r') as file:
                tracked_files = ast.literal_eval(file.read())

            # removing temp_dir
            if os.path.exists(temp_dir):
                os.remove(temp_dir)

            """
            object_name contains the path of the .dir on the artifact repo
            we need to remove the hash of the .dir from the object_name
            which will leave us with the artifact repo path
            """
            # Parse host URL to extract the path
            parsed_url = urlparse(host)
            repo_path = "/".join(parsed_url.path.split("/")[:-2])

            for file_info in tracked_files:
                total_files_in_directory += 1
                relpath = file_info['relpath']
                
                # Validate relpath to prevent path traversal attacks
                # Normalize the path and ensure it doesn't escape the download directory
                normalized_relpath = os.path.normpath(relpath)
                
                # Reject absolute paths
                if os.path.isabs(normalized_relpath):
                    logger.error(f"  |-- [SECURITY] Rejected absolute path in .dir metadata: {relpath}")
                    continue
                
                # Reject paths that try to traverse up (e.g., ../)
                # Old POSIX-specific check (replaced for platform independence):
                # if normalized_relpath.startswith('..') or '/..' in normalized_relpath:
                # Use Path.parts for platform-independent check (works on both POSIX and Windows)
                if '..' in Path(normalized_relpath).parts:
                    logger.error(f"  |-- [SECURITY] Rejected path traversal attempt in .dir metadata: {relpath}")
                    continue
                
                md5_val = file_info['md5']
                # md5_val = a237457aa730c396e5acdbc5a64c8453
                # we need a2/37457aa730c396e5acdbc5a64c8453
                formatted_md5 = md5_val[:2] + '/' + md5_val[2:]
                temp_download_loc = os.path.join(abs_download_loc, normalized_relpath)
                
                # Final safety check: ensure temp_download_loc is within abs_download_loc
                # Resolve to absolute paths and check containment
                abs_temp_download_loc = os.path.abspath(temp_download_loc)
                abs_base_dir = os.path.abspath(abs_download_loc)
                if not abs_temp_download_loc.startswith(abs_base_dir + os.sep) and abs_temp_download_loc != abs_base_dir:
                    logger.error(f"  |-- [SECURITY] Resolved path escapes download directory: {relpath}")
                    continue
                
                # Construct the full URL for the file (origin)
                parsed_host_url = urlparse(host)
                temp_host = f"{parsed_host_url.scheme}://{parsed_host_url.netloc}{repo_path}/{formatted_md5}"
                
                try:
                    # Create subdirectories if needed
                    temp_dir_path = os.path.dirname(abs_temp_download_loc)
                    if temp_dir_path:
                        os.makedirs(temp_dir_path, mode=0o777, exist_ok=True)
                    
                    # Download with cache fallback to origin
                    success, result = self._download_with_cache_fallback(
                        temp_host, cache, abs_temp_download_loc, abs_temp_download_loc, md5_val
                    )
                    if success:
                        files_downloaded += 1
                        #logger.info(f"  |-- {relpath} -> {abs_temp_download_loc}")
                        logger.info(f"  |-- {normalized_relpath}")
                    else:
                        logger.error(f"  |-- [FAILED] {normalized_relpath}")
                except Exception as e:
                    logger.exception(f"  |-- [FAILED] {relpath} due to unexpected error")

            # total_files - files_downloaded gives us the number of files which failed to download
            if (total_files_in_directory - files_downloaded) == 0:   
                return total_files_in_directory, files_downloaded, True
            return total_files_in_directory, files_downloaded, False
        except Exception as e:
            logger.error(f"[download_directory] object {object_name} is not downloaded. Error: {e}")
            # We usually don't count .dir as a file while counting total_files_in_directory.
            # However, here we failed to download the .dir folder itself. 
            # So we need to make, total_files_in_directory = 1
            total_files_in_directory = 1 
            return total_files_in_directory, files_downloaded, False
        

        