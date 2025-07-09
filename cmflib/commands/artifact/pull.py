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

#!/usr/bin/env python3
import os
import argparse

from cmflib import cmfquery
from cmflib.storage_backends import (
    minio_artifacts,
    local_artifacts,
    amazonS3_artifacts,
    sshremote_artifacts,
    osdf_artifacts,
)
from cmflib.cli.command import CmdBase
from cmflib.cmf_exception_handling import (
    PipelineNotFound, 
    FileNotFound, 
    MissingArgument,
    ExecutionsNotFound, 
    ArtifactNotFound, 
    BatchDownloadFailure, 
    BatchDownloadSuccess,
    ObjectDownloadFailure, 
    ObjectDownloadSuccess,
    DuplicateArgumentNotAllowed,
    MsgSuccess,
    MsgFailure
)
from cmflib.utils.helper_functions import fetch_cmf_config_path

class CmdArtifactPull(CmdBase):
    def split_url_pipeline(self, url: str, pipeline_name: str):
       # This function takes url and pipeline_name as a input parameter
       # return string which contains the artifact repo path of the artifact
       # url = Test-env:/home/user/local-storage/files/md5/23/6d9502e0283d91f689d7038b8508a2
       # pipeline_name = Test-env

       # checking whether pipeline name exist inside url
       if pipeline_name in url:
            # if multiple pipelines logs same artifact, then spliting them using ',' delimiter 
            if "," in url:
                urls = url.split(",")
                # iterate over each urls
                for u in urls:
                    # assign u to url if pipeline name exist
                    if pipeline_name in u:
                        url = u
            # splitting url using ':' delimiter 
            # token = ["Test-env","home/user/local-storage/files/md5/23/6d9502e508a2"]
            token = url.split(":")
            # removing 1st element from token i.e pipeline name
            # output token will be ["home/user/local-storage/files/md5/23/6d9502e508a2"]
            token.pop(0)
            if len(token) > 1:
                # in case of metrics we have multiple ':' in its url
                # concating remaining tokens after removing pipeline_name using ':' delimiter
                token_str = ":".join(token)
                return token_str
            return "".join(token)

    def extract_repo_args(self, type: str, name: str, url: str, current_directory: str):
        # Extracting the repository URL, current path, bucket name, and other relevant
        # information from the user-supplied arguments.
        # url = Test-env:/home/user/local-storage/files/md5/06/d100ff3e04e2c87bf20f0feacc9034,
        #          Second-env:/home/user/local-storage/files/md5/06/d100ff3e04e2c"
        # s_url = Url without pipeline name
        s_url = self.split_url_pipeline(url, self.args.pipeline_name[0])

        # got url in the form of /home/user/local-storage/files/md5/06/d100ff3e04e2c
        # spliting url using '/' delimiter
        token = s_url.split("/")

        # name = artifacts/model/model.pkl
        name = name.split(":")[0]
        if type == "minio":
            token_length = len(token)

            # assigned 2nd position element to bucket_name
            bucket_name = token[2]

            # The folder structure of artifact data has been updated due to a change in the DVC 3.0 version
            # Previously, the structure was dvc-art/23/69v2uu3jeejjeiw
            # but now it includes additional directories and has become files dvc-art/files/md5/23/69v2uu3jeejjeiw.
            # Consequently, the previous logic takes only the last 2 elements from the list of tokens,
            # but with the new structure, it needs to take the last 4 elements.

            # get last 4 element inside token
            token = token[(token_length-4):]

            # join last 4 token using '/' delimiter
            object_name = "/".join(token)
            # output = files/md5/23/69v2uu3jeejjeiw

            path_name = current_directory + "/" + name
            return bucket_name, object_name, path_name

        elif type == "local":
            token_length = len(token)
            download_loc = current_directory + "/" + name
            # local artifact repo path =  local-storage/files/md5/23/69v2uu3jeejjeiw.
            # token is a list = ['local-storage', 'files', 'md5', '23', '69v2uu3jeejjeiw']
            # get last 4 element inside token
            token = token[(token_length-4):]
            # join last 4 token using '/' delimiter
            current_dvc_loc = "/".join(token)
            return current_dvc_loc, download_loc

        elif type == "ssh":
            # token = ['ssh:', '', 'XX.XX.XX.XX:22', 'home', 'user', 'ssh-storage', 'files', 'md5', '23', '6d9502e0283d91f689d7038b8508a2']
            host_with_port = token[2].split(":")
            host = host_with_port[0]
            # Update token list by removing the first three items
            # token = ['home', 'user', 'ssh-storage', 'files', 'md5', '23', '6d9502e0283d91f689d7038b8508a2']
            current_loc = '/' + '/'.join(token[3:])
            return host, current_loc, name
        
        elif type == "osdf":
            token_length = len(token)
            download_loc = current_directory + "/" + name if current_directory != ""  else name
            #current_dvc_loc = (token[(token_length - 2)] + "/" + token[(token_length - 1)])
            #return FQDNL of where to download from, where to download to, what the artifact will be named
            return s_url, download_loc, name
        else:
            # sometimes s_url is empty - this shouldn't happen technically
            # sometimes s_url is not starting with s3:// - technically this shouldn't happen
            if s_url and s_url.startswith("s3://"):
                url_with_bucket = s_url.split("s3://")[1]
                # url_with_bucket = mybucket/user/files/md5/23/6d9502e0283d91f689d7038b8508a2
                # splitting the string using '/' as the delimiter
                # bucket_name = mybucket
                # object_name = user/files/md5/23/6d9502e0283d91f689d7038b8508a2
                bucket_name, object_name = url_with_bucket.split('/', 1)
                download_loc =  current_directory + "/" + name if current_directory != ""  else name
                #print(download_loc)
                return bucket_name, object_name, download_loc
            else:
                # returning bucket_name, object_name and download_loc returning as empty
                return "", "", ""

    def search_artifact(self, input_dict, remote):
        flag = True
        artifact_name = self.args.artifact_name[0]
        
        # This function takes input_dict as input artifact
        for name, url in input_dict.items():
            if not isinstance(url, str):
                continue
            # Splitting the 'name' using ':' as the delimiter and storing the first argument in the 'file_path' variable.
            # eg name = ./a/data.xml.gz:12345abcd -->  a/data.xml.gz
            file_path = name.split(":")[0]
            # Splitting the path on '/' to extract the file name, excluding the directory structure.
            # eg name = ./a/data.xml.gz --> data.xml.gz
            file_name = file_path.split('/')[-1]
           
            if remote == "osdf":
                # Extracting the artifact hash from the artifact name.
                artifact_hash = name = name.split(":")[1]
                return name, url, artifact_hash
            elif name == artifact_name or file_path == artifact_name or file_name == artifact_name:
                # If the artifact name matches, set flag to False and break the loop
                flag = False
                break
            
        if flag:
            # Raise an exception if the artifact is not found
            raise ArtifactNotFound(artifact_name)
        return name, url

    def run(self, live):
        output, config_file_path = fetch_cmf_config_path()
        
        cmd_args = {
            "file_name": self.args.file_name,
            "pipeline_name": self.args.pipeline_name,
            "artifact_name": self.args.artifact_name
        }
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))
                
        # check whether 'mlmd' file exist in current directory 
        # or in the directory provided by user
        # pipeline_name = self.args.pipeline_name
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if "/" not in mlmd_file_name:
                mlmd_file_name = "./"+mlmd_file_name
        current_directory = os.path.dirname(mlmd_file_name)

        if not self.args.artifact_name:         # If self.args.artifact_name[0] is None or an empty list ([]). 
            pass
        
        if not os.path.exists(mlmd_file_name):   #checking if MLMD files exists
            raise FileNotFound(mlmd_file_name, current_directory)
        query = cmfquery.CmfQuery(mlmd_file_name)
        
        pipeline_name = self.args.pipeline_name[0]
        if not pipeline_name in query.get_pipeline_names():   #checking if pipeline name exists in mlmd
            raise PipelineNotFound(pipeline_name)
        
        # getting all pipeline stages[i.e Prepare, Featurize, Train and Evaluate]
        stages = query.get_pipeline_stages(pipeline_name)
        executions = []
        identifiers = []
        for stage in stages:
            # getting all executions for stages
            executions = query.get_all_executions_in_stage(stage)
            # check if stage has executions
            if len(executions) > 0:
                 # converting it to dictionary
                dict_executions = executions.to_dict("dict")
                # append id's of executions inside identifiers
                for id in dict_executions["id"].values():
                    identifiers.append(id)
            else:
                print("No Executions found for " + stage + " stage.")
        # created dictionary
        name_url_dict = {}
        if len(identifiers) == 0:  # check if there are no executions
            raise ExecutionsNotFound()
        for identifier in identifiers:
            get_artifacts = query.get_all_artifacts_for_execution(
                identifier
            )  # getting all artifacts with id
            # skipping artifacts if it is type of label
            temp_dict = {
                name: url
                for name, url, artifact_type in zip(get_artifacts['name'], get_artifacts['url'], get_artifacts['type'])
                if artifact_type != "Label"
            }
            name_url_dict.update(temp_dict) # updating name_url_dict with temp_dict
        # name_url_dict = ('artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81', 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81'
        # name_url_dict = ('artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81', 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81,Second-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81')
        """
           There are multiple scenarios for cmf artifact pull 
           Code checks if self.args.artifact_name[0] is provided by user or not
           under these conditions there are two more conditions
              1. if file is not .dir (single file) 
                   Download single file
              2. else file is .dir (directory)
                   download all files from directory
                     
        """
        dvc_config_op = output
        if dvc_config_op["core.remote"] == "minio":
            minio_class_obj = minio_artifacts.MinioArtifacts(dvc_config_op)
            # Check if a specific artifact name is provided as input.
            if self.args.artifact_name: 
                # Search for the artifact in the metadata store.
                # If the artifact is not found, an error will be raised automatically.
                output = self.search_artifact(name_url_dict, dvc_config_op["core.remote"])
                # output[0] = artifact_name
                # output[1] = url
                # output[2] = hash
                # Extract repository arguments specific to MinIO.
                minio_args = self.extract_repo_args("minio", output[0], output[1], current_directory)

                # Check if the object name doesn't end with `.dir` (indicating it's a file).
                if not minio_args[1].endswith(".dir"):
                    # Download a single file from MinIO.
                    object_name, download_loc, download_flag = minio_class_obj.download_file(
                        current_directory,
                        minio_args[0], # bucket_name
                        minio_args[1], # object_name
                        minio_args[2], # path_name
                    )
                    if download_flag:
                        # Return success if the file is downloaded successfully.
                        return ObjectDownloadSuccess(object_name, download_loc)
                    raise ObjectDownloadFailure(object_name)
                else:
                    # If object name ends with `.dir`, download multiple files from a directory 
                    # return total_files_in_directory, files_downloaded
                    total_files_in_directory, dir_files_downloaded, download_flag = minio_class_obj.download_directory(
                        current_directory,
                        minio_args[0], # bucket_name
                        minio_args[1], # object_name
                        minio_args[2], # path_name
                    )
        
                    if download_flag:
                        # Return success if all files in the directory are downloaded.
                        return BatchDownloadSuccess(dir_files_downloaded)
                    # Calculate the number of files that failed to download.
                    file_failed_to_download = total_files_in_directory - dir_files_downloaded
                    raise BatchDownloadFailure(dir_files_downloaded, file_failed_to_download)
            
            else:
                # Handle the case where no specific artifact name is provided.
                files_downloaded = 0
                files_failed_to_download = 0

                # Iterate through the dictionary of artifact names and URLs.
                for name, url in name_url_dict.items():
                    if not isinstance(url, str):    ## Skip invalid URLs.
                        continue
                    minio_args = self.extract_repo_args("minio", name, url, current_directory)

                    # Check if the object name doesn't end with `.dir` (indicating it's a file).
                    if not minio_args[1].endswith(".dir"):
                        # Download a single file from MinIO.
                        object_name, download_loc, download_flag = minio_class_obj.download_file(
                            current_directory,
                            minio_args[0], # bucket_name
                            minio_args[1], # object_name
                            minio_args[2], # path_name
                        )

                        # print output here because we are in a loop and can't return the control
                        if download_flag:
                            print(f"object {object_name} downloaded at {download_loc}.")
                            files_downloaded += 1
                        else:
                            print(f"object {object_name} is not downloaded.")
                            files_failed_to_download += 1
                    else:
                        # If object name ends with `.dir`, download multiple files from a directory.
                        total_files_in_directory, dir_files_downloaded, download_flag = minio_class_obj.download_directory(
                            current_directory,
                            minio_args[0], # bucket_name
                            minio_args[1], # object_name
                            minio_args[2], # path_name
                        )
                        # Return success if all files in the directory are downloaded.
                        if download_flag:
                            files_downloaded += dir_files_downloaded
                        else:
                            files_downloaded += dir_files_downloaded
                            files_failed_to_download += (total_files_in_directory - dir_files_downloaded)
                            
                # we are assuming, if files_failed_to_download > 0, it means our download of artifacts is not success
                if not files_failed_to_download:
                    return BatchDownloadSuccess(files_downloaded)
                raise BatchDownloadFailure(files_downloaded, files_failed_to_download)

        elif dvc_config_op["core.remote"] == "local-storage":
            local_class_obj = local_artifacts.LocalArtifacts(dvc_config_op)
            # There are two main conditions
            # Condition 1 - user can use -a paramter for cmf artifact pull command
                # -a can be a dir or a file
            # Condition 2 - user can chose to download all the artifacts in one go. 
                # we can have both dir and files in our list of artifacts
            # Check if a specific artifact name is provided as input.
            if self.args.artifact_name:
                # Search for the artifact in the metadata store.
                # If the artifact is not found, an error will be raised automatically.
                output = self.search_artifact(name_url_dict, dvc_config_op["core.remote"])
                # output[0] = name
                # output[1] = url
                # Extract repository arguments specific to Local repo.
                local_args = self.extract_repo_args("local", output[0], output[1], current_directory)
                # local_args [0] = current_dvc_loc
                # local_args [1] = download_loc
                # Check if the object name doesn't end with `.dir` (indicating it's a file).
                if not local_args[0].endswith(".dir"):
                    # Download a single file from Local.
                    object_name, download_loc, download_flag = local_class_obj.download_file(current_directory, local_args[0], local_args[1])
                    if download_flag:
                        # Return success if the file is downloaded successfully.
                        return ObjectDownloadSuccess(object_name, download_loc)
                    raise ObjectDownloadFailure(object_name)
                    
                else:
                    # If object name ends with `.dir`, download multiple files from a directory 
                    # return total_files_in_directory, files_downloaded
                    total_files_in_directory, dir_files_downloaded, download_flag = local_class_obj.download_directory(current_directory, local_args[0], local_args[1])
        
                    if download_flag:
                        # Return success if all files in the directory are downloaded.
                        return BatchDownloadSuccess(dir_files_downloaded)
                    # Calculate the number of files that failed to download.
                    file_failed_to_download = total_files_in_directory - dir_files_downloaded
                    raise BatchDownloadFailure(dir_files_downloaded, file_failed_to_download)
            else:
                # Handle the case where no specific artifact name is provided.
                files_downloaded = 0
                files_failed_to_download = 0
                # Iterate through the dictionary of artifact names and URLs.
                for name, url in name_url_dict.items():
                    if not isinstance(url, str):
                        continue
                    # name1 - file
                    # name2 - failed file
                    # name3 - dir (5 files)
                    # name4 - dir (4 files) - failed dir - 2 files passed, 2 files failed
                    # name5 - file
                    # name6 - dir - and can't open it (but it has 2 files) .. user don't know 
                    local_args = self.extract_repo_args("local", name, url, current_directory)
                    # local_args [0] = current_dvc_loc
                    # local_args [1] = download_loc
                    # Check if the object name doesn't end with `.dir` (indicating it's a file).
                    if not local_args[0].endswith(".dir"):
                        # Download a single file from Local repo.
                        object_name, download_loc, download_flag = local_class_obj.download_file(
                            current_directory, local_args[0], local_args[1])
                        
                        # print output here because we are in a loop and can't return the control
                        if download_flag:
                            print(f"object {object_name} downloaded at {download_loc}.")
                            files_downloaded += 1
                        else:
                            print(f"object {object_name} is not downloaded.")
                            files_failed_to_download += 1
                    else:
                        # If object name ends with `.dir`, download multiple files from a directory.
                        total_files_in_directory, dir_files_downloaded, download_flag = local_class_obj.download_directory(
                            current_directory, local_args[0], local_args[1])
                        # download_flag is true only when all the files from the directory are successfully downlaoded.
                        if download_flag:
                            files_downloaded += dir_files_downloaded
                        else:
                            files_downloaded += dir_files_downloaded
                            files_failed_to_download += (total_files_in_directory - dir_files_downloaded)
                            
                # we are assuming, if files_failed_to_download > 0, it means our download of artifacts is not success
                if not files_failed_to_download:
                    return BatchDownloadSuccess(files_downloaded)
                raise BatchDownloadFailure(
                            files_downloaded, files_failed_to_download)
                    
        elif dvc_config_op["core.remote"] == "ssh-storage":
            sshremote_class_obj = sshremote_artifacts.SSHremoteArtifacts(dvc_config_op)
            # Check if a specific artifact name is provided as input.
            if self.args.artifact_name:
                # Search for the artifact in the metadata store.
                # If the artifact is not found, an error will be raised automatically.
                output = self.search_artifact(name_url_dict, dvc_config_op["core.remote"])
                # output[0] = name
                # output[1] = url
                # Extract repository arguments specific to ssh-remote.
                args = self.extract_repo_args("ssh", output[0], output[1], current_directory)
                # Check if the object name doesn't end with `.dir` (indicating it's a file).
                if not args[1].endswith(".dir"):
                    # Download a single file from ssh-remote.
                    object_name, download_loc, download_flag = sshremote_class_obj.download_file(
                        args[0], # host,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2]  # name
                    )
                    if download_flag:
                        # Return success if the file is downloaded successfully.
                        return ObjectDownloadSuccess(object_name, download_loc)
                    raise ObjectDownloadFailure(object_name)

                else:
                    # If object name ends with `.dir`, download multiple files from a directory 
                    # return total_files_in_directory, files_downloaded
                    total_files_in_directory, dir_files_downloaded, download_flag = sshremote_class_obj.download_directory(
                        args[0], # host,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2]  # name
                        )
                if download_flag:
                    # Return success if all files in the directory are downloaded.
                    return BatchDownloadSuccess(dir_files_downloaded)
                # Calculate the number of files that failed to download.
                file_failed_to_download = total_files_in_directory - dir_files_downloaded
                raise BatchDownloadFailure(dir_files_downloaded, file_failed_to_download)   
            else:
                # Handle the case where no specific artifact name is provided.
                files_downloaded = 0
                files_failed_to_download = 0
                # Iterate through the dictionary of artifact names and URLs.
                for name, url in name_url_dict.items():
                    if not isinstance(url, str):
                        continue
                    args = self.extract_repo_args("ssh", name, url, current_directory)
                    # Check if the object name doesn't end with `.dir` (indicating it's a file).
                    if not args[1].endswith(".dir"):
                        # Download a single file from ssh-remote.
                        object_name, download_loc, download_flag = sshremote_class_obj.download_file(
                        args[0], # host,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2]  # name
                    )
                        # print output here because we are in a loop and can't return the control
                        if download_flag:
                            print(f"object {object_name} downloaded at {download_loc}.")
                            files_downloaded += 1
                        else:
                            print(f"object {object_name} is not downloaded.")
                            files_failed_to_download += 1
                    else:
                        # If object name ends with `.dir`, download multiple files from a directory.
                        total_files_in_directory, dir_files_downloaded, download_flag = sshremote_class_obj.download_directory(
                            args[0], # host,
                            current_directory,
                            args[1], # remote_loc of the artifact
                            args[2]  # name
                        )
                        if download_flag:
                            files_downloaded += dir_files_downloaded
                        else:
                            files_downloaded += dir_files_downloaded
                            files_failed_to_download += (total_files_in_directory - dir_files_downloaded)
                            
                # we are assuming, if files_failed_to_download > 0, it means our download of artifacts is not success
                if not files_failed_to_download:
                    return BatchDownloadSuccess(files_downloaded)
                raise BatchDownloadFailure(files_downloaded, files_failed_to_download)
        elif dvc_config_op["core.remote"] == "osdf":
            #Regenerate Token for OSDF
            from cmflib.utils.helper_functions import generate_osdf_token
            from cmflib.dvc_wrapper import dvc_add_attribute
            from cmflib.utils.cmf_config import CmfConfig
            #Fetch Config from CMF_Config_File
            cmf_config_file = os.environ.get("CONFIG_FILE", ".cmfconfig")
            cmf_config={}
            cmf_config=CmfConfig.read_config(cmf_config_file)
            #Regenerate password 
            dynamic_password = generate_osdf_token(cmf_config["osdf-key_id"],cmf_config["osdf-key_path"],cmf_config["osdf-key_issuer"])
            #cmf_config["password"]=dynamic_password
            #Update Password in .dvc/config for future use
            dvc_add_attribute(dvc_config_op["core.remote"],"password",dynamic_password)
            #Updating dvc_config_op data structure with new password as well since this is used in download_artifacts() below
            dvc_config_op["remote.osdf.password"]=dynamic_password
            #Need to write to cmfconfig with new credentials
            #CmfConfig.write_config(cmf_config, "osdf", attr_dict, True)
            #Now Ready to do dvc pull 
            cache_path=cmf_config["osdf-cache"]

            osdfremote_class_obj = osdf_artifacts.OSDFremoteArtifacts()
            if self.args.artifact_name:
                # Search for the artifact in the metadata store.
                # If the artifact is not found, an error will be raised automatically.
                output = self.search_artifact(name_url_dict, dvc_config_op["core.remote"])
                # output[0] = name
                # output[1] = url
                # output[3]=artifact_hash
                args = self.extract_repo_args("osdf", output[0], output[1], current_directory)
                download_flag, message = osdfremote_class_obj.download_artifacts(
                    dvc_config_op,
                    args[0], # s_url of the artifact
                    cache_path,
                    current_directory,
                    args[1], # download_loc of the artifact
                    args[2],  # name of the artifact
                    output[3] #Artifact Hash
                )
                
                if download_flag :
                    status = MsgSuccess(msg_str = message)
                else:
                    status = MsgFailure(msg_str = message)
                return status
            else:
                for name, url in name_url_dict.items():
                    total_files_count += 1
                    #print(name, url)
                    if not isinstance(url, str):
                        continue
                    artifact_hash = name.split(':')[1] #Extract Hash of the artifact from name
                    #print(f"Hash for the artifact {name} is {artifact_hash}")
                    args = self.extract_repo_args("osdf", name, url, current_directory)
                        
                    download_flag, message = osdfremote_class_obj.download_artifacts(
                        dvc_config_op,
                        args[0], # host,
                        cache_path,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2],  # name
                        artifact_hash #Artifact Hash
                    )
                    if download_flag:
                        print(message)   #### success message
                        file_downloaded +=1
                    else:
                        print(message)    ### failure message
                Files_failed_to_download = total_files_count - files_downloaded
                if Files_failed_to_download == 0:
                    status = BatchDownloadSuccess(files_downloaded=files_downloaded)
                else:
                    status = BatchDownloadFailure(files_downloaded=files_downloaded, Files_failed_to_download= Files_failed_to_download)
                return status
        elif dvc_config_op["core.remote"] == "amazons3":
            amazonS3_class_obj = amazonS3_artifacts.AmazonS3Artifacts(dvc_config_op)
            if self.args.artifact_name:
                # Search for the artifact in the metadata store.
                # If the artifact is not found, an error will be raised automatically.
                output = self.search_artifact(name_url_dict, dvc_config_op["core.remote"])
                # output[0] = name
                # output[1] = url
                args = self.extract_repo_args("amazons3", output[0], output[1], current_directory)
                if args[0] and args[1] and args[2]:
                    if not args[1].endswith(".dir"):
                        object_name, download_loc, download_flag = amazonS3_class_obj.download_file(
                            current_directory,
                            args[0], # bucket_name
                            args[1], # object_name
                            args[2], # download_loc
                        )
                        if download_flag:
                            return ObjectDownloadSuccess(object_name, download_loc)
                        raise ObjectDownloadFailure(object_name)
                    else:
                        total_files_in_directory, dir_files_downloaded, download_flag = amazonS3_class_obj.download_directory(current_directory,
                            args[0], # bucket_name
                            args[1], # object_name
                            args[2], # download_loc
                            )
                    if download_flag:
                        return BatchDownloadSuccess(dir_files_downloaded)
                    file_failed_to_download = total_files_in_directory - dir_files_downloaded
                    raise BatchDownloadFailure(dir_files_downloaded, file_failed_to_download)
        
            else:
                files_downloaded = 0
                files_failed_to_download = 0
                for name, url in name_url_dict.items():
                    if not isinstance(url, str):
                        continue
                    args = self.extract_repo_args("amazons3", name, url, current_directory)
                    if args[0] and args[1] and args[2]:
                        if not args[1].endswith(".dir"):
                            object_name, download_loc, download_flag = amazonS3_class_obj.download_file(
                                current_directory,
                                args[0], # bucket_name
                                args[1], # object_name
                                args[2], # download_loc
                            )
                            if download_flag:
                                print(f"object {object_name} downloaded at {download_loc}.")
                                files_downloaded += 1
                            else:
                                print(f"object {object_name} is not downloaded.")
                                files_failed_to_download += 1
                        else:
                            total_files_in_directory, dir_files_downloaded, download_flag = amazonS3_class_obj.download_directory(
                            current_directory,
                            args[0], # bucket_name
                            args[1], # object_name
                            args[2], # path_name
                        )
                        # download_flag is true only when all the files from the directory are successfully downlaoded.
                            if download_flag:
                                files_downloaded += dir_files_downloaded
                            else:
                                files_downloaded += dir_files_downloaded
                                files_failed_to_download += (total_files_in_directory - dir_files_downloaded)
                            
                # we are assuming, if files_failed_to_download > 0, it means our download of artifacts is not success
                if not files_failed_to_download:
                    return BatchDownloadSuccess(files_downloaded)
                raise BatchDownloadFailure(files_downloaded, files_failed_to_download)
        else:
            remote = dvc_config_op["core.remote"]
            msg = f"{remote} is not valid artifact repository for CMF.\n Reinitialize CMF."
            raise MsgFailure(msg_str=msg)


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pull artifacts from user configured repository."

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="Pull artifacts from user configured repository.",
        help=PULL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-p",
        "--pipeline_name",
        required=True,
        action="append",
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-f", "--file_name", action="append", help="Specify input metadata file name.", metavar="<file_name>"
    )

    parser.add_argument(
        "-a", "--artifact_name", action="append", help="Specify artifact name.", metavar="<artifact_name>"
    )

    parser.set_defaults(func=CmdArtifactPull)

