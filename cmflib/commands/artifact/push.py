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
import re
import argparse

from cmflib import cmfquery
from cmflib.cli.utils import find_root
from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import dvc_push
from cmflib.utils.dvc_config import DvcConfig
from cmflib.utils.cmf_config import CmfConfig
from cmflib.cli.utils import check_minio_server
from cmflib.dvc_wrapper import dvc_add_attribute
from cmflib.utils.helper_functions import generate_osdf_token
from cmflib.cmf_exception_handling import (
    PipelineNotFound, Minios3ServerInactive, 
    FileNotFound, 
    ExecutionsNotFound, 
    CmfNotConfigured, 
    ArtifactPushSuccess, 
    MissingArgument, 
    DuplicateArgumentNotAllowed
)

class CmdArtifactPush(CmdBase):
    def run(self, live):
        result = ""
        dvc_config_op = DvcConfig.get_dvc_config()
        cmf_config_file = os.environ.get("CONFIG_FILE", ".cmfconfig")

        # find root_dir of .cmfconfig
        output = find_root(cmf_config_file)

        # in case, there is no .cmfconfig file
        if output.find("'cmf' is not configured.") != -1:
            raise CmfNotConfigured(output)
        
        cmd_args = {
            "file_name": self.args.file_name,
            "pipeline_name": self.args.pipeline_name
        }
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))

        out_msg = check_minio_server(dvc_config_op)
        if dvc_config_op["core.remote"] == "minio" and out_msg != "SUCCESS":
            raise Minios3ServerInactive()
        if dvc_config_op["core.remote"] == "osdf":
            config_file_path = os.path.join(output, cmf_config_file)
            cmf_config={}
            cmf_config=CmfConfig.read_config(config_file_path)
            #print("key_id="+cmf_config["osdf-key_id"])
            dynamic_password = generate_osdf_token(cmf_config["osdf-key_id"],cmf_config["osdf-key_path"],cmf_config["osdf-key_issuer"])
            #print("Dynamic Password"+dynamic_password)
            dvc_add_attribute(dvc_config_op["core.remote"],"password",dynamic_password)
            #The Push URL will be something like: https://<Path>/files/md5/[First Two of MD5 Hash]
            result = dvc_push()
            #print(result)
            return result

        # Default path of mlmd file
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            raise FileNotFound(mlmd_file_name, current_directory)
        
        # creating cmfquery object
        query = cmfquery.CmfQuery(mlmd_file_name)
        
        pipeline_name = self.args.pipeline_name[0]
        # Put a check to see whether pipline exists or not
        if not query.get_pipeline_id(pipeline_name) > 0:
            raise PipelineNotFound(pipeline_name)

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
                for id in dict_executions["id"].values():
                    identifiers.append(id)
            else:
                print("No Executions found for " + stage + " stage.")

        names = []
        if len(identifiers) == 0:  # check if there are no executions
            raise ExecutionsNotFound()
        for identifier in identifiers:
            artifacts = query.get_all_artifacts_for_execution(
                 identifier
            )  # getting all artifacts with id
            # dropping artifact with type 'metrics' as metrics doesn't have physical file
            if not artifacts.empty:
                artifacts = artifacts[artifacts['type'] != 'Metrics']
                # adding .dvc at the end of every file as it is needed for pull
                artifacts['name'] = artifacts['name'].apply(lambda name: f"{name.split(':')[0]}.dvc")
                names.extend(artifacts['name'].tolist())
        final_list = []
        for file in set(names):
            # checking if the .dvc exists
            if os.path.exists(file):
                final_list.append(file)
            # checking if the .dvc exists in user's project working directory
            elif os.path.isabs(file):
                    file = re.split("/",file)[-1]
                    file = os.path.join(os.getcwd(), file)
                    if os.path.exists(file):
                        final_list.append(file)
            else:
                # not adding the .dvc to the final list in case .dvc doesn't exists in both the places
                pass
        result = dvc_push(list(final_list))
        return ArtifactPushSuccess(result)
    
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
        action="append",
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-f", 
        "--file_name", 
        action="append",
        help="Specify input metadata file name.",
        metavar="<file_name>"
    )

    parser.set_defaults(func=CmdArtifactPush)
