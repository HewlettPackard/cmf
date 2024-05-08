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
import subprocess

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.cli.utils import check_minio_server
from cmflib.utils.dvc_config import DvcConfig
from cmflib.dvc_wrapper import dvc_push


class CmdArtifactPush(CmdBase):
    def run(self):
        result = ""
        dvc_config_op = DvcConfig.get_dvc_config()
        out_msg = check_minio_server(dvc_config_op)
        if dvc_config_op["core.remote"] == "minio" and out_msg != "SUCCESS":
            return out_msg

        current_directory = os.getcwd()
        # Default path of mlmd file
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."
 
        # creating cmfquery object
        query = cmfquery.CmfQuery(mlmd_file_name)

         # Put a check to see whether pipline exists or not
        pipeline_name = self.args.pipeline_name
        if not query.get_pipeline_id(pipeline_name) > 0:
            return f"ERROR: Pipeline {pipeline_name} doesn't exist!!"

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

        names = []
        if len(identifiers) == 0:  # check if there are no executions
            return "No executions found."
        for identifier in identifiers:
            artifacts = query.get_all_artifacts_for_execution(
                 identifier
            )  # getting all artifacts with id
            art_list = artifacts['name'].tolist()
            names.extend(artifacts['name'].tolist())

        print(names)
        count = 0
        for name in names:
            temp = f"{name.split(':')[0]}.dvc"
            res = dvc_push(temp)
            count += 1
        return f"{count} files pushed!!"


def add_parser(subparsers, parent_parser):
    HELP = "Push artifacts to the user configured artifact repo."

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push artifacts to the user configured artifact repo.",
        help=HELP,
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

    parser.set_defaults(func=CmdArtifactPush)
