###
# Copyright (2022) Hewlett Packard Enterprise Development LP
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

from cmflib import cmf_merger
from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.utils.cmf_config import CmfConfig
from cmflib.utils.helper_functions import fetch_cmf_config_path
from cmflib.server_interface import server_interface
from cmflib.cmf_exception_handling import (
    DuplicateArgumentNotAllowed,
    PipelineNotFound,
    MissingArgument,
    ExecutionUUIDNotFound,
    MlmdNotFoundOnServer,
    MlmdFilePullSuccess,
    DirectoryNotfound,
    FileNameNotfound,
    ExecutionsAlreadyExists,
    UpdateCmfVersion,
)
from cmflib.cmf_federation import update_mlmd

# This class pulls mlmd file from cmf-server
class CmdMetadataPull(CmdBase):

    def run(self, live):
        output, cmf_config_path = fetch_cmf_config_path()
        
        attr_dict = CmfConfig.read_config(cmf_config_path)
        url = attr_dict.get("cmf-server-url", "http://127.0.0.1:80")
        current_directory = os.getcwd()
        full_path_to_dump = ""
        cmd = "pull"
        status = 0
        exec_uuid = None

        cmd_args = {
            "file_name": self.args.file_name,
            "pipeline_name": self.args.pipeline_name,
            "execution_uuid": self.args.execution_uuid
        }  
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))
        
        if not self.args.execution_uuid:         # If self.args.execution_uuid[0] is None or an empty list ([]). 
            pass
         
        if self.args.file_name:  # setting directory where mlmd file will be dumped
            if not os.path.isdir(self.args.file_name[0]):
                temp = os.path.dirname(self.args.file_name[0])
                if temp != "":
                    current_directory = temp
                if os.path.exists(current_directory):
                    full_path_to_dump  = self.args.file_name[0]
                else:
                    raise DirectoryNotfound(dir = current_directory)
            else:
                raise FileNameNotfound
        else:
            full_path_to_dump = os.getcwd() + "/mlmd"
         
        query = cmfquery.CmfQuery(full_path_to_dump)
        if self.args.execution_uuid:
            exec_uuid = self.args.execution_uuid[0]

        query = cmfquery.CmfQuery(full_path_to_dump)
        output = server_interface.call_mlmd_pull(
            url, self.args.pipeline_name[0], exec_uuid
        )  # calls cmf-server api to get mlmd file data(Json format)
         
        status = output.status_code
        # Checks if given pipeline does not exist
        # or if the execution UUID not present inside the mlmd file
        # else pulls the mlmd file
        if status == 404:
            raise PipelineNotFound(self.args.pipeline_name[0])
        elif output.content.decode() == "no_exec_uuid":
            raise ExecutionUUIDNotFound(exec_uuid)
        else:
            response = update_mlmd(query, output.content, self.args.pipeline_name[0], "pull", exec_uuid)
            if response =="success":
                return MlmdFilePullSuccess(full_path_to_dump)
            elif response == "exists":
                return ExecutionsAlreadyExists()
            elif response == "invalid_json_payload":
                raise MlmdNotFoundOnServer
            elif response == "version_update":
                raise UpdateCmfVersion
            
def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pulls metadata from cmf-server to users's machine."

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="Pulls metadata from cmf-server to users's machine.",
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
        "-f",
        "--file_name",
        action="append",
        help="Specify output metadata file name.",
        metavar="<file_name>",
    )

    parser.add_argument(
        "-e", "--execution_uuid", action="append", help="Specify execution_uuid", metavar="<exec_uuid>"
    )

    parser.set_defaults(func=CmdMetadataPull)
