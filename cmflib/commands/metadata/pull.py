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
import argparse
import os
from cmflib import cmf_merger
from cmflib.cli.command import CmdBase
from cmflib.cli.utils import find_root
from cmflib.server_interface import server_interface
from cmflib.utils.cmf_config import CmfConfig
from cmflib.cmf_exception_handling import (
    DuplicateArgumentNotAllowed,
    PipelineNotFound,
    MissingArgument,
    CmfNotConfigured, 
    ExecutionUUIDNotFound,
    MlmdNotFoundOnServer,
    MlmdFilePullSuccess,
    CmfServerNotAvailable, 
    InternalServerError,
    MlmdFilePullFailure,
    DirectoryNotfound,
    FileNameNotfound
)

# This class pulls mlmd file from cmf-server
class CmdMetadataPull(CmdBase):

    def run(self):
        cmfconfig = os.environ.get("CONFIG_FILE", ".cmfconfig")
        # find root_dir of .cmfconfig
        output = find_root(cmfconfig)
        # in case, there is no .cmfconfig file
        if output.find("'cmf' is not configured") != -1:
            raise CmfNotConfigured(output)
        config_file_path = os.path.join(output, cmfconfig)
        attr_dict = CmfConfig.read_config(config_file_path)
        url = attr_dict.get("cmf-server-ip", "http://127.0.0.1:80")
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
                    raise DirectoryNotfound(current_dir= current_directory)
            else:
                raise FileNameNotfound
        else:
            full_path_to_dump = os.getcwd() + "/mlmd"
        
        if self.args.execution_uuid:
            exec_uuid = self.args.execution_uuid[0]
        output = server_interface.call_mlmd_pull(
            url, self.args.pipeline_name[0], exec_uuid
        )  # calls cmf-server api to get mlmd file data(Json format)
        status = output.status_code
        # checks If given pipeline does not exists/ elif pull mlmd file/ else mlmd file is not available
        if output.content.decode() == None:
            raise PipelineNotFound(self.args.pipeline_name[0])
        elif output.content.decode() == "no_exec_uuid":
            raise ExecutionUUIDNotFound(exec_uuid)
      
        elif output.content:
            if status == 200:
                try:
                    cmf_merger.parse_json_to_mlmd(
                        output.content, full_path_to_dump, cmd, exec_uuid
                    )  # converts mlmd json data to mlmd file
                    pull_status = MlmdFilePullSuccess(full_path_to_dump)
                    return pull_status
                except Exception as e:
                    return e
            elif status == 413:
                raise MlmdNotFoundOnServer
            elif status == 406:
                raise PipelineNotFound(self.args.pipeline_name[0])
            elif status == 404:
                raise CmfServerNotAvailable
            elif status == 500:
                raise InternalServerError
            else:
                raise MlmdFilePullFailure
            
def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pulls mlmd from cmf-server to users's machine."

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="Pulls mlmd from cmf-server to users's machine.",
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
        help="Specify mlmd file name with full path.",
        metavar="<file_name>",
    )

    parser.add_argument(
        "-e", "--execution_uuid", action="append", help="Specify execution_uuid", metavar="<exec_uuid>"
    )

    parser.set_defaults(func=CmdMetadataPull)
