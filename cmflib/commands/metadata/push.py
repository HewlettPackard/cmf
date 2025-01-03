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
import json

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.cli.utils import find_root
from cmflib.server_interface import server_interface
from cmflib.utils.cmf_config import CmfConfig
from cmflib.cmf_exception_handling import (
    TensorboardPushSuccess, 
    TensorboardPushFailure, 
    MlmdFilePushSuccess,
    ExecutionsAlreadyExists,
    FileNotFound,
    ExecutionIDNotFound,
    PipelineNotFound,
    UpdateCmfVersion,
    CmfServerNotAvailable,
    InternalServerError,
    CmfNotConfigured,
    InvalidTensorboardFilePath,
    MissingArgument,
    DuplicateArgumentNotAllowed
)
# This class pushes mlmd file to cmf-server
class CmdMetadataPush(CmdBase):
    def run(self):
        # Get url from config
        cmfconfig = os.environ.get("CONFIG_FILE",".cmfconfig")

        # find root_dir of .cmfconfig
        output = find_root(cmfconfig)

        # in case, there is no .cmfconfig file
        if output.find("'cmf' is not configured.") != -1:
            raise CmfNotConfigured(output)

        config_file_path = os.path.join(output, cmfconfig)
        attr_dict = CmfConfig.read_config(config_file_path)
        url = attr_dict.get("cmf-server-ip", "http://127.0.0.1:80")

        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        elif len(self.args.file_name) > 1:  # If the user provided more than one file name. 
            raise DuplicateArgumentNotAllowed("file_name", "-f")
        elif not self.args.file_name[0]:    # self.args.file_name[0] is an empty string (""). 
            raise MissingArgument("file name")
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        
        current_directory = os.path.dirname(mlmd_file_name)
        
        # checks if mlmd file is present in current directory or given directory
        if not os.path.exists(mlmd_file_name):
            raise FileNotFound(mlmd_file_name, current_directory)

        query = cmfquery.CmfQuery(mlmd_file_name)
        # print(json.dumps(json.loads(json_payload), indent=4, sort_keys=True))
        execution_flag = 0
        status_code = 0

        # Checks if pipeline name exists
        if self.args.pipeline_name is not None and len(self.args.pipeline_name) > 1:  
            raise DuplicateArgumentNotAllowed("pipeline_name", "-p")
        elif not self.args.pipeline_name[0]:    # self.args.pipeline_name[0] is an empty string ("").   
            raise MissingArgument("pipeline name")
        else:
            pipeline_name = self.args.pipeline_name[0]
            if pipeline_name in query.get_pipeline_names():
                print("metadata push started")
                print("........................................")
                # converts mlmd file to json format
                json_payload = query.dumptojson(pipeline_name, None)
                
                # checks if execution is given by user
                if not self.args.execution:         # If self.args.execution is None or an empty list ([]).
                    exec_id = None
                    response = server_interface.call_mlmd_push(json_payload, url, exec_id, pipeline_name)
                elif len(self.args.execution) > 1:  # If the user provided more than one execution.  
                    raise DuplicateArgumentNotAllowed("execution", "-e")
                elif not self.args.execution[0]:    # self.args.execution[0] is an empty string ("").
                    raise MissingArgument("execution id")
                elif not self.args.execution[0].isdigit():
                    raise ExecutionIDNotFound(self.args.execution[0])
                else:
                    exec_id = int(self.args.execution[0])
                    mlmd_data = json.loads(json_payload)["Pipeline"]
                    # checks if given execution present in mlmd
                    for i in mlmd_data[0]["stages"]:
                        for j in i["executions"]:
                            if j["id"] == int(exec_id):
                                execution_flag = 1
                                # calling mlmd_push api to push mlmd file to cmf-server
                                response = server_interface.call_mlmd_push(
                                    json_payload, url, exec_id, pipeline_name
                                )
                                break
                    if execution_flag == 0:
                        raise ExecutionIDNotFound(exec_id)
                status_code = response.status_code
                if status_code == 200:
                    output = ""
                    display_output = ""
                    if response.json()['status']=="success":
                        display_output = "mlmd is successfully pushed."
                        output = MlmdFilePushSuccess(mlmd_file_name)
                    if response.json()["status"]=="exists":
                        display_output = "Executions already exists."
                        output = ExecutionsAlreadyExists()

                    if not self.args.tensorboard:
                        return output
                    elif len(self.args.tensorboard) > 1:  # If the user provided more than one tensorboard name. 
                        raise DuplicateArgumentNotAllowed("tensorboard", "-t")
                    elif not self.args.tensorboard[0]:    # self.args.tensorboard[0] is an empty string (""). 
                        raise MissingArgument("tensorboard")
                    print(display_output)
                    # /tensorboard api call is done only if mlmd push is successfully completed
                    # tensorboard parameter is passed
                    print("......................................")
                    print("tensorboard logs upload started!!")
                    print("......................................")

                    tensorboard = self.args.tensorboard[0]
                    # check if the path provided is for a file
                    if os.path.isfile(tensorboard):
                        file_name = os.path.basename(tensorboard)
                        tresponse = server_interface.call_tensorboard(url, pipeline_name, file_name, tensorboard)
                        tstatus_code = tresponse.status_code
                        if tstatus_code == 200:
                            # give status code as success
                            return TensorboardPushSuccess(file_name)
                        else:
                            # give status code as failure 
                            return TensorboardPushFailure(file_name,tresponse.text)
                    # If path provided is a directory
                    elif os.path.isdir(tensorboard):
                        # Recursively push all files and subdirectories
                        for root, dirs, files in os.walk(tensorboard):
                            for file_name in files:
                                file_path = os.path.join(root, file_name)
                                relative_path = os.path.relpath(file_path, tensorboard)
                                tresponse = server_interface.call_tensorboard(url, pipeline_name, relative_path, file_path)
                                if tresponse.status_code == 200:
                                    print(f"tensorboard logs: File {file_name} uploaded successfully.")
                                else:
                                    # give status as failure
                                    return TensorboardPushFailure(file_name,tresponse.text)
                        return TensorboardPushSuccess()
                    else:
                        return InvalidTensorboardFilePath()
                elif status_code==422 and response.json()["status"]=="version_update":
                    raise UpdateCmfVersion
                elif status_code == 404:
                    raise CmfServerNotAvailable
                elif status_code == 500:
                    raise InternalServerError
                else:
                    return "ERROR: Status Code = {status_code}. Unable to push mlmd."
            else:
                raise PipelineNotFound(pipeline_name)


def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Push user-generated mlmd to server to create one single mlmd file for all the pipelines."

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push user's mlmd to cmf-server.",
        help=PUSH_HELP,
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
        help="Specify mlmd file name.", 
        metavar="<file_name>"
    )

    parser.add_argument(
        "-e",
        "--execution",
        action="append",
        help="Specify Execution id.",
        metavar="<exec_id>",
    )

    parser.add_argument(
        "-t",
        "--tensorboard",
        action="append",
        help="Specify path to tensorboard logs for the pipeline.",
        metavar="<tensorboard>"
    )

    parser.set_defaults(func=CmdMetadataPush)
