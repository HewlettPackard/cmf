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
import argparse
import os

from cmflib import cmfquery
from cmflib.storage_backends import (
    minio_artifacts,
    local_artifacts,
    amazonS3_artifacts,
    sshremote_artifacts,
    osdf_artifacts,
)
from cmflib.cli.command import CmdBase
from cmflib.utils.dvc_config import DvcConfig


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
            # splitting url using ':' delimiter token = ["Test-env","home/user/local-storage/files/md5/23/6d9502e508a2"]
            token = url.split(":")
            # removing 1st element from token i.e pipeline name
            # output token will be ["home/user/local-storage/files/md5/23/6d9502e508a2"]
            token.pop(0)
            if len(token) > 1:
                # in case of metrics we have multiple ':' in its url
                # concating remaining tokens after removing pipeline_name using ':' delimiter
                token = ":".join(token)
                return token
            return "".join(token)

    def extract_repo_args(self, type: str, name: str, url: str, current_directory: str):
        # Extracting the repository URL, current path, bucket name, and other relevant
        # information from the user-supplied arguments.
        # url = Test-env:/home/user/local-storage/files/md5/06/d100ff3e04e2c87bf20f0feacc9034,
        #          Second-env:/home/user/local-storage/files/md5/06/d100ff3e04e2c"

        # s_url = Url without pipeline name
        s_url = self.split_url_pipeline(url, self.args.pipeline_name)

        # got url in the form of /home/user/local-storage/files/md5/06/d100ff3e04e2c
        #spliting url using '/' delimiter
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

            # get last 4 element inside token
            token = token[(token_length-4):]

            # join last 4 token using '/' delimiter
            current_dvc_loc = "/".join(token)

            return current_dvc_loc, download_loc

        elif type == "ssh":
            # comments remaining
            token_var = token[2].split(":")
            host = token_var[0]
            token.pop(0)
            token.pop(0)
            token.pop(0)
            current_loc_1 = "/".join(token)
            current_loc = f"/{current_loc_1}"
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

    def search_artifact(self, input_dict):
        # This function takes input_dict as input artifact
        for name, url in input_dict.items():
            if not isinstance(url, str):
                continue
            # splitting name with ':' as the delimiter and store first argument inside name
            name = name.split(":")[0]
            file_name = name.split('/')[-1]
            if file_name == self.args.artifact_name:
                return name, url
            else:
                pass

    def run(self):
        # check whether the mlmd file exist or not in current directory
        pipeline_name = self.args.pipeline_name
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."
        query = cmfquery.CmfQuery(mlmd_file_name)

        # getting all pipeline stages[i.e Prepare, Featurize, Train and Evaluate]
        stages = query.get_pipeline_stages(self.args.pipeline_name)
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
            return "No executions found."
        for identifier in identifiers:
            get_artifacts = query.get_all_artifacts_for_execution(
                identifier
            )  # getting all artifacts with id
            temp_dict = dict(zip(get_artifacts['name'], get_artifacts['url'])) # getting dictionary of name and url pair
            name_url_dict.update(temp_dict) # updating name_url_dict with temp_dict
        # print(name_url_dict)
        # name_url_dict = ('artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81', 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81'
        # name_url_dict = ('artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81', 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81,Second-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81')

        output = DvcConfig.get_dvc_config()  # pulling dvc config
        if type(output) is not dict:
            return output
        dvc_config_op = output

        if dvc_config_op["core.remote"] == "minio":
            minio_class_obj = minio_artifacts.MinioArtifacts()
            if self.args.artifact_name:
                output = self.search_artifact(name_url_dict)
                # output[0] = name
                # output[1] = url
                if output is None:
                    print(f"{self.args.artifact_name} doesn't exist.")
                else:
                    minio_args = self.extract_repo_args("minio", output[0], output[1], current_directory)
                    stmt = minio_class_obj.download_artifacts(
                        dvc_config_op,
                        current_directory,
                        minio_args[0], # bucket_name
                        minio_args[1], # object_name
                        minio_args[2], # path_name
                    )
                    print(stmt)
            else:
                for name, url in name_url_dict.items():
                    if not isinstance(url, str):
                        continue
                    minio_args = self.extract_repo_args("minio", name, url, current_directory)
                    stmt = minio_class_obj.download_artifacts(
                        dvc_config_op,
                        current_directory,
                        minio_args[0], # bucket_name
                        minio_args[1], # object_name
                        minio_args[2], # path_name
                    )
                    print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "local-storage":
            local_class_obj = local_artifacts.LocalArtifacts()
            if self.args.artifact_name:
                output = self.search_artifact(name_url_dict)
                # output[0] = name
                # output[1] = url
                if output is None:
                    print(f"{self.args.artifact_name} doesn't exist.")
                else:
                    local_args = self.extract_repo_args("local", output[0], output[1], current_directory)
                    stmt = local_class_obj.download_artifacts(
                           dvc_config_op, current_directory, local_args[0], local_args[1]
                    )
                    print(stmt)
            else:
                for name, url in name_url_dict.items():
                    #print(name, url)
                    if not isinstance(url, str):
                        continue
                    local_args = self.extract_repo_args("local", name, url, current_directory)
                    # local_args[0] = current dvc location
                    # local_args[1] = current download location
                    stmt = local_class_obj.download_artifacts(
                           dvc_config_op, current_directory, local_args[0], local_args[1]
                    )
                    print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "ssh-storage":
            sshremote_class_obj = sshremote_artifacts.SSHremoteArtifacts()
            if self.args.artifact_name:
                output = self.search_artifact(name_url_dict)
                # output[0] = name
                # output[1] = url
                if output is None:
                    print(f"{self.args.artifact_name} doesn't exist.")
                else:
                    args = self.extract_repo_args("ssh", output[0], output[1], current_directory)
                    stmt = sshremote_class_obj.download_artifacts(
                        dvc_config_op,
                        args[0], # host,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2]  # name
                    )
                    print(stmt)
            else:
                for name, url in name_url_dict.items():
                    #print(name, url)
                    if not isinstance(url, str):
                        continue
                    args = self.extract_repo_args("ssh", name, url, current_directory)
                    stmt = sshremote_class_obj.download_artifacts(
                        dvc_config_op,
                        args[0], # host,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2]  # name
                    )
                    print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "osdf":
            #Regenerate Token for OSDF
            from cmflib.utils.helper_functions import generate_osdf_token
            from cmflib.utils.helper_functions import is_url
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

            osdfremote_class_obj = osdf_artifacts.OSDFremoteArtifacts()
            if self.args.artifact_name:
                output = self.search_artifact(name_url_dict)
                # output[0] = name
                # output[1] = url
                if output is None:
                    print(f"{self.args.artifact_name} doesn't exist.")
                else:
                    args = self.extract_repo_args("osdf", output[0], output[1], current_directory)
                    stmt = osdfremote_class_obj.download_artifacts(
                        dvc_config_op,
                        args[0], # s_url of the artifact
                        current_directory,
                        args[1], # download_loc of the artifact
                        args[2]  # name of the artifact
                    )
                    print(stmt)
            else:
                for name, url in name_url_dict.items():
                    #print(name, url)
                    if not isinstance(url, str):
                        continue
                    args = self.extract_repo_args("osdf", name, url, current_directory)
                    stmt = osdfremote_class_obj.download_artifacts(
                        dvc_config_op,
                        args[0], # host,
                        current_directory,
                        args[1], # remote_loc of the artifact
                        args[2]  # name
                    )
                    print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "amazons3":
            amazonS3_class_obj = amazonS3_artifacts.AmazonS3Artifacts()
            #print(self.args.artifact_name,"artifact name")
            if self.args.artifact_name:
                output = self.search_artifact(name_url_dict)
                # output[0] = name
                # output[1] = url
                if output is None:
                    print(f"{self.args.artifact_name} doesn't exist.")
                else:
                    args = self.extract_repo_args("amazons3", output[0], output[1], current_directory)
                    if args[0] and args[1] and args[2]:
                        stmt = amazonS3_class_obj.download_artifacts(
                            dvc_config_op,
                            current_directory,
                            args[0], # bucket_name
                            args[1], # object_name
                            args[2], # download_loc
                        )
                        print(stmt)
            else:
                for name, url in name_url_dict.items():
                    if not isinstance(url, str):
                        continue
                    args = self.extract_repo_args("amazons3", name, url, current_directory)
                    if args[0] and args[1] and args[2]:
                        stmt = amazonS3_class_obj.download_artifacts(
                            dvc_config_op,
                            current_directory,
                            args[0], # bucket_name
                            args[1], # object_name
                            args[2], # download_loc
                        )
                        print(stmt)
            return "Done"
        else:
            remote = dvc_config_op["core.remote"]
            msg = f"{remote} is not valid artifact repository for CMF.\n Reinitialize CMF."
            return msg


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
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>"
    )

    parser.add_argument(
        "-a", "--artifact_name", help="Specify artifact name.", metavar="<artifact_name>"
    )

    parser.set_defaults(func=CmdArtifactPull)

