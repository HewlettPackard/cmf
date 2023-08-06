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

    def split_url_pipeline(self, url: str, pipeline_name: str): 
        if pipeline_name in url:
            if "," in url:
                urls = url.split(",")
                for u in urls:
                    if pipeline_name in u:
                        url = u
            temp = url.split(":")
            temp.pop(0)
            if len(temp) > 1:
                temp = ":".join(temp)
                return temp
            return "".join(temp)

    def run(self):
        # Put a check to see whether pipline exists or not
        pipeline_name = self.args.pipeline_name
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
            # getting all executions for stages
            executions = query.get_all_executions_in_stage(stage)
            # check if stage has executions
            if len(executions) > 0:
                 # converting it to dictionary
                dict_executions = executions.to_dict("dict")
                for id in dict_executions["id"].values():
                    identifiers.append(id)
            else:
                print("No Executions found for " + stage + " stage.")

        name_url_dict = {}
        if len(identifiers) == 0:  # check if there are no executions
            return "No executions found."
        for identifier in identifiers:
            get_artifacts = query.get_all_artifacts_for_execution(
                identifier
            )  # getting all artifacts with id
            temp_dict = dict(zip(get_artifacts['name'], get_artifacts['url']))
            name_url_dict.update(temp_dict)
        #print(name_url_dict)
        # name_url_dict = ('artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81', 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81'
        # name_url_dict = ('artifacts/parsed/test.tsv:6f597d341ceb7d8fbbe88859a892ef81', 'Test-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81,Second-env:/home/sharvark/local-storage/6f/597d341ceb7d8fbbe88859a892ef81')

        output = DvcConfig.get_dvc_config()  # pulling dvc config
        if type(output) is not dict:
            return output
        dvc_config_op = output

        if dvc_config_op["core.remote"] == "minio":
            minio_class_obj = minio_artifacts.MinioArtifacts()
            for name, url in name_url_dict.items():
                if not isinstance(url, str):
                    continue
                # url = 'Test-env:s3://dvc-art/6f/597d341ceb7d8fbbe88859a892ef81,Second-env:s3://dvc-art/6f/597d341ceb7d8fbbe88859a892ef81')
                s_url = self.split_url_pipeline(url, pipeline_name)
                # s_url = s3://dvc-art/6f/597d341ceb7d8fbbe88859a892ef81
                temp = s_url.split("/")
                bucket_name = temp[2]
                object_name = temp[3] + "/" + temp[4]
                name = name.split(":")[0]
                # name = 'artifacts/parsed/test.tsv'
                path_name = current_directory + "/" + name
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
            for name, url in name_url_dict.items():
                if not isinstance(url, str):
                    continue
                # url = 'Test-env:/home/user/local-storage/06/d100ff3e04e2c87bf20f0feacc9034,Second-env:/home/user/local-storage/06/d100ff3e04e2c87bf20f0feacc9034'
                s_url = self.split_url_pipeline(url, pipeline_name)
                temp = s_url.split("/")
                temp_length = len(temp)
                name = name.split(":")[0]
                # name = artifacts/model/model.pkl
                download_loc = current_directory + "/" + name
                current_dvc_loc = (
                    temp[(temp_length - 2)] + "/" + temp[(temp_length - 1)]
                )
                stmt = local_class_obj.download_artifacts(
                    dvc_config_op, current_directory, current_dvc_loc, name
                )
                print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "ssh-storage":
            sshremote_class_obj = sshremote_artifacts.SSHremoteArtifacts()
            for name, url in name_url_dict.items():
                if not isinstance(url, str):
                    continue
                # url = 'Test-env:ssh://127.0.0.1/home/user/ssh-storage/06/d100ff3e04e2c87bf20f0feacc9034'
                s_url = self.split_url_pipeline(url, pipeline_name)
                temp = s_url.split("/")
                temp_var = temp[2].split(":")
                host = temp_var[0]
                name = name.split(":")[0]
                # name = artifacts/model/model.pkl
                download_loc = current_directory + "/" + name
                temp.pop(0)
                temp.pop(0)
                temp.pop(0)
                current_loc_1 = "/".join(temp)
                current_loc = f"/{current_loc_1}"
                stmt = sshremote_class_obj.download_artifacts(
                    dvc_config_op, host, current_directory, current_loc, name
                )
                print(stmt)
            return "Done"
        elif dvc_config_op["core.remote"] == "amazons3":
            amazonS3_class_obj = amazonS3_artifacts.AmazonS3Artifacts()
            for name_url in name_url_dict.items():
                if not isinstance(url, str):
                    continue
                # url ='Test-env:s3://XXXXXXX/dvc-art/6f/597d341ceb7d8fbbe88859a892ef81'
                s_url = self.split_url_pipeline(url, pipeline_name)
                temp = s_url.split("/")
                bucket_name = temp[2]
                object_name = f"{temp[3]}/{temp[4]}/{temp[5]}"
                name = name.split(":")[0]
                # name = artifacts/model/model.pkl
                download_loc = current_directory + "/" + name
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

    parser.add_argument(
        "-a", "--artifact_name", help="Specify artifact name.", metavar="<artifact_name>"
    )

    parser.set_defaults(func=CmdArtifactPull)
