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
import requests
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import hashlib
import time

from urllib.parse import urlparse

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
        print(f"An error occurred while reading the file: {e}")
        return None
    return md5.hexdigest()

def download_and_verify_file(host, headers, remote_file_path, local_path, artifact_hash, timeout):
    print(f"Fetching artifact={local_path}, surl={host} to {remote_file_path}")
    data= None
    try:
        response = requests.get(host, headers=headers, timeout=timeout, verify=True)  # This should be made True. otherwise this will produce Insecure SSL Warning
        if response.status_code == 200 and response.content:
            data = response.content
        else:
            return False, "No data received from the server."
            #pass
    except requests.exceptions.Timeout:
        return False, "The request timed out."
        #pass
    except Exception as exception:
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
                    #print(f"MD5 hash of the downloaded file is: {md5_hash}")
                    #print(f"Time taken to calculate MD5 hash: {time_taken:.2f} seconds")
                    if artifact_hash == md5_hash:
                        #print("MD5 hash of the downloaded file matches the hash in MLMD records.")
                        stmt = f"object {local_path} downloaded at {remote_file_path} in {time_taken:.2f} seconds and matches MLMD records."
                        success=True
                    else:
                        #print("Error: MD5 hash of the downloaded file does not match the hash in MLMD records.")
                        stmt = f"object {local_path} downloaded at {remote_file_path} in {time_taken:.2f} seconds and does NOT match MLMD records."
                        success=False
                    return success, stmt
                else:
                    print("Failed to calculate MD5 hash of the downloaded file.")
        except Exception as e:
            print(f"An error occurred while writing to the file: {e}")
            return False, f"An error occurred while writing to the file: {e}"
    
    return False, "Data is None."


class OSDFremoteArtifacts:
    def download_artifacts(
        self,
        dvc_config_op,
        host: str, #s_url 
        cache: str, #cache_path from cmfconfig
        current_directory: str, #current_directory where cmf artifact pull is executed
        remote_file_path: str, # download_loc of the artifact 
        local_path: str, #name of the artifact
        artifact_hash: str, #hash of the artifact from MLMD records
    ):
        #print(f"Configured Host from MLMD record={host}. User configured cache redirector={cache}")
        output = ""
        remote_repo = dvc_config_op["remote.osdf.url"]
        user = "nobody"
        dynamic_password = dvc_config_op["remote.osdf.password"]
        custom_auth_header = dvc_config_op["remote.osdf.custom_auth_header"]
        #print(f"dynamic password from download_artifacts={dynamic_password}")
        #print(f"Fetching artifact={local_path}, surl={host} to {remote_file_path} when this has been called at {current_directory}")

        # Prepare directories and file paths
        headers={dvc_config_op["remote.osdf.custom_auth_header"]: dvc_config_op["remote.osdf.password"]}
        temp = local_path.split("/")
        temp.pop()
        dir_path = "/".join(temp)
        dir_to_create = os.path.join(current_directory, dir_path)
        os.makedirs(
            dir_to_create, mode=0o777, exist_ok=True
        )  # creates subfolders needed as per artifacts folder structure
        local_file_path = os.path.join(current_directory, local_path)
        local_file_path = os.path.abspath(local_file_path)
        
        #Cache can be Blank. If so, fetch from Origin
        if cache == "":
            #Fetch from Origin
            success, result = download_and_verify_file(host, headers, remote_file_path, local_file_path, artifact_hash, timeout=10)
            if success:
                #print(result)
                return success, result
            #print(f"Failed to download and verify file: {result}")
            return success, f"Failed to download and verify file: {result}"
        else:
            #Generate Cached path for artifact
            cached_s_url=generate_cached_url(host,cache)
            #Try to fetch from cache first
            success, cached_result = download_and_verify_file(cached_s_url, headers, remote_file_path, local_path, artifact_hash,timeout=5)
            if success:
                #print(cached_result)
                return success, cached_result
            else:
                print(f"Failed to download and verify file from cache: {cached_result}")
                print(f"Trying Origin at {host}")
                #Fetch from Origin 
                success, origin_result = download_and_verify_file(host, headers, remote_file_path, local_path, artifact_hash, timeout=10)
                if success: 
                    #print(origin_result)
                    return success, origin_result
                #print(f"Failed to download and verify file: {result}")
                return success, f"Failed to download and verify file: {origin_result}"
        

        