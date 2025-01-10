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
    InvalidTensorboardFilePath
)
# This class pushes mlmd file to cmf-server
class CmdMetadataPush(CmdBase):

    # Create a function to search for files into multiple directories
    def search_files(self, file_list, *directories):
        found_files = {}
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            for file_name in file_list:
                if isinstance(file_name, str):
                    file_path = os.path.join(abs_dir, file_name)
                    if os.path.isfile(file_path):
                        found_files[file_name] = file_path
        return found_files

    def run(self):
        current_directory = mlmd_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
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

        # checks if mlmd filepath is given
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            mlmd_directory = os.path.dirname(self.args.file_name)

        # checks if mlmd file is present in current directory or given directory
        if not os.path.exists(mlmd_file_name):
            raise FileNotFound(mlmd_file_name, mlmd_directory)

        query = cmfquery.CmfQuery(mlmd_file_name)
        # print(json.dumps(json.loads(json_payload), indent=4, sort_keys=True))
        status_code = 0

        # Checks if pipeline name exists
        if self.args.pipeline_name in query.get_pipeline_names():
            execution = None
            exec_id = None
            if self.args.execution:
                # this is not the correct way to type cast as this is user given input 
                execution = query.get_all_executions_by_ids_list([int(self.args.execution)])
                if execution.empty:
                    raise ExecutionIDNotFound(exec_id)
                exec_id = int(self.args.execution)
            # converts mlmd file to json format
            json_payload = query.dumptojson(self.args.pipeline_name, None)
            response = server_interface.call_mlmd_push(json_payload, url, exec_id, self.args.pipeline_name)
            status_code = response.status_code

            # we need to push the python env files only after the mlmd push has succeded 
            # otherwise there is no use of those python env files on cmf-server

            if status_code==422 and response.json()["status"]=="version_update":
                raise UpdateCmfVersion
            elif status_code == 404:
                raise CmfServerNotAvailable
            elif status_code == 500:
                raise InternalServerError
            elif status_code == 200:
                # the only question remains how we want to percieve the failure of upload of the python env files 
                # for now, it is considered as non-consequential.
                # that means it's failure/success doesn't matter.
                # however, we will be keeping the record of the status code.
                
                # Getting all executions df to get the custom property 'Python_Env'
                executions = query.get_all_executions_in_pipeline(self.args.pipeline_name)
                if not executions.empty:
                    if 'custom_properties_Python_Env' in executions.columns:
                        list_of_env_files = executions['custom_properties_Python_Env'].drop_duplicates().tolist()
                        # This is a validation step to suppress errors in case user is pushing the mlmd
                        # from a directory in which 'cmf_artifacts/Python_Env_hash.txt' is not present.
                        # Find the valid file paths.  
                        found_files = self.search_files(list_of_env_files, current_directory, mlmd_directory) 

                        # push valid files on cmf-server
                        if found_files:
                            for name, path in found_files.items():
                                env_response = server_interface.call_python_env(url, name, path)
                                # keeping record of status but this won't affect the mlmd success.
                                print(env_response.json())

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
                print(display_output)
                # /tensorboard api call is done only if mlmd push is successfully completed
                # tensorboard parameter is passed
                print("......................................")
                print("tensorboard logs upload started!!")
                print("......................................")
                # check if the path provided is for a file
                if os.path.isfile(self.args.tensorboard):
                    file_name = os.path.basename(self.args.tensorboard)
                    tresponse = server_interface.call_tensorboard(url, self.args.pipeline_name, file_name, self.args.tensorboard)
                    tstatus_code = tresponse.status_code
                    if tstatus_code == 200:
                        # give status code as success
                        return TensorboardPushSuccess(file_name)
                    else:
                        # give status code as failure 
                        return TensorboardPushFailure(file_name,tresponse.text)
                # If path provided is a directory            
                elif os.path.isdir(self.args.tensorboard):
                    # Recursively push all files and subdirectories
                    for root, dirs, files in os.walk(self.args.tensorboard):
                        for file_name in files:
                            file_path = os.path.join(root, file_name)
                            relative_path = os.path.relpath(file_path, self.args.tensorboard)
                            tresponse = server_interface.call_tensorboard(url, self.args.pipeline_name, relative_path, file_path)
                            if tresponse.status_code == 200:
                                print(f"tensorboard logs: File {file_name} uploaded successfully.")
                            else:
                                # give status as failure
                                return TensorboardPushFailure(file_name,tresponse.text)
                    return TensorboardPushSuccess()
                else:
                    return InvalidTensorboardFilePath()   
            else:
                return "ERROR: Status Code = {status_code}. Unable to push mlmd."
        else:
            raise PipelineNotFound(self.args.pipeline_name)


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
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>"
    )

    parser.add_argument(
        "-e",
        "--execution",
        help="Specify Execution id.",
        metavar="<exec_id>",
    )

    parser.add_argument(
        "-t",
        "--tensorboard",
        help="Specify path to tensorboard logs for the pipeline.",
        metavar="<tensorboard>"
    )

    parser.set_defaults(func=CmdMetadataPush)
