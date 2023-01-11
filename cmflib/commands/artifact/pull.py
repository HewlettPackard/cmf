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
)
from cmflib.cli.command import CmdBase
from cmflib.utils.dvc_config import DvcConfig


class CmdArtifactPull(CmdBase):
    def run(self):
        # Put a check to see whether pipline exists or not
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            current_directory = os.path.dirname(self.args.file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."
        query = cmfquery.CmfQuery(mlmd_file_name)
        stages = query.get_pipeline_stages(self.args.pipeline_name)
        executions = []
        identifiers = []
        for stage in stages:
            executions = query.get_all_executions_in_stage(
                stage
            )  # getting all executions for stages
            if len(executions) > 0:  # check if stage has executions
                dict_executions = executions.to_dict(
                    "dict"
                )  # converting it to dictionary
                identifiers.append(dict_executions["id"][0])  # id's of execution
            else:
                print("No Executions found for " + stage + " stage.")
        name = []
        url = []
        if len(identifiers) == 0:  # check if there are no executions
            return "No executions found."
        for identifier in identifiers:
            get_artifacts = query.get_all_artifacts_for_execution(
                identifier
            )  # getting all artifacts with id
            artifacts_dict = get_artifacts.to_dict(
                "dict"
            )  # converting it to dictionary
            name.append(list(artifacts_dict["name"].values()))
            url.append(list(artifacts_dict["url"].values()))
        name_list_updated = [name for l in name for name in l]  # getting names and urls
        url_list_updated = [url for l in url for url in l]
        final_list = []
        file_name = [(i.split(":"))[0] for i in name_list_updated]  # getting names
        for i in tuple(zip(file_name, url_list_updated)):
            if type(i[1]) == str:
                final_list.append(i)
        names_urls = list(set(final_list))  # list of tuple consist of names and urls
        # names_urls = ('artifacts/model/model.pkl', '/home/user/local-storage/06/d100ff3e04e2c87bf20f0feacc9034')
        print(names_urls)
        output = DvcConfig.get_dvc_config()  # pulling dvc config
        if type(output) is not dict:
            return output
        dvc_config_op = output
        if dvc_config_op["core.remote"] == "minio":
            minio_class_obj = minio_artifacts.MinioArtifacts()
            for name_url in names_urls:
                # name_url[1] = 's3://dvc-art/6f/597d341ceb7d8fbbe88859a892ef81')
                temp = name_url[1].split("/")
                bucket_name = temp[2]
                object_name = temp[3] + "/" + temp[4]
                # name_url[0] = 'artifacts/parsed/test.tsv'
                path_name = current_directory + "/" + name_url[0]
                stmt = minio_class_obj.download_artifacts(
                    dvc_config_op,
                    current_directory,
                    bucket_name,
                    object_name,
                    path_name,
                )
                print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "local-storage":
            local_class_obj = local_artifacts.LocalArtifacts()
            for name_url in names_urls:
                # name_url[1] = '/home/user/local-storage/06/d100ff3e04e2c87bf20f0feacc9034'
                temp = name_url[1].split("/")
                temp_length = len(temp)
                # name_url[0] = artifacts/model/model.pkl
                download_loc = current_directory + "/" + name_url[0]
                current_dvc_loc = (
                    temp[(temp_length - 2)] + "/" + temp[(temp_length - 1)]
                )
                stmt = local_class_obj.download_artifacts(
                    dvc_config_op, current_directory, current_dvc_loc, name_url[0]
                )
                print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "ssh-storage":
            sshremote_class_obj = sshremote_artifacts.SSHremoteArtifacts()
            for name_url in names_urls:
                # name_url[1] = ssh://127.0.0.1/home/user/ssh-storage/06/d100ff3e04e2c87bf20f0feacc9034
                temp = name_url[1].split("/")
                temp_var = temp[2].split(":")
                host = temp_var[0]
                # name_url[0] = artifacts/model/model.pkl
                download_loc = current_directory + "/" + name_url[0]
                temp.pop(0)
                temp.pop(0)
                temp.pop(0)
                current_loc_1 = "/".join(temp)
                current_loc = f"/{current_loc_1}"
                stmt = sshremote_class_obj.download_artifacts(
                    dvc_config_op, host, current_directory, current_loc, name_url[0]
                )
                print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "amazons3":
            amazonS3_class_obj = amazonS3_artifacts.AmazonS3Artifacts()
            for name_url in names_urls:
                # name_url[1] = s3://XXXXXXX/dvc-art/6f/597d341ceb7d8fbbe88859a892ef81'
                temp = name_url[1].split("/")
                bucket_name = temp[2]
                object_name = f"{temp[3]}/{temp[4]}/{temp[5]}"
                # name_url[0] = artifacts/model/model.pkl
                download_loc = current_directory + "/" + name_url[0]
                stmt = amazonS3_class_obj.download_artifacts(
                    dvc_config_op,
                    current_directory,
                    bucket_name,
                    object_name,
                    download_loc,
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

    parser.set_defaults(func=CmdArtifactPull)
