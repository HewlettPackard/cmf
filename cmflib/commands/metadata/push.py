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
    ExecutionUUIDNotFound,
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

        cmd_args = {
            "file_name": self.args.file_name,
            "pipeline_name": self.args.pipeline_name,
            "execution_uuid": self.args.execution_uuid,
            "tensorboad": self.args.tensorboard
        }  
        for arg_name, arg_value in cmd_args.items():
            if arg_value:
                if arg_value[0] == "":
                    raise MissingArgument(arg_name)
                elif len(arg_value) > 1:
                    raise DuplicateArgumentNotAllowed(arg_name,("-"+arg_name[0]))
         

        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        
        current_directory = os.path.dirname(mlmd_file_name)
        
        # checks if mlmd file is present in current directory or given directory
        if not os.path.exists(mlmd_file_name):
            raise FileNotFound(mlmd_file_name, mlmd_directory)

        query = cmfquery.CmfQuery(mlmd_file_name)
        # print(json.dumps(json.loads(json_payload), indent=4, sort_keys=True))
        status_code = 0

        # Checks if pipeline name exists
        pipeline_name = self.args.pipeline_name[0]
        if pipeline_name in query.get_pipeline_names():
            print("metadata push started")
            print("........................................")
            # converts mlmd file to json format
            json_payload = query.dumptojson(pipeline_name, None)

            # checks if execution is given by user
            if not self.args.execution_uuid:         # If self.args.execution_uuid is None or an empty list ([]).
                exec_uuid = None
                response = server_interface.call_mlmd_push(json_payload, url, exec_uuid, pipeline_name)
            else:
                exec_uuid = self.args.execution_uuid[0]
                mlmd_data = json.loads(json_payload)["Pipeline"]
                # checks if given execution present in mlmd
                for i in mlmd_data[0]["stages"]:
                    for j in i["executions"]:
                        # created exec_uuid of list if multiple uuid present for single execution.
                        # for eg: f9da581c-d16c-11ef-9809-9350156ed1ac,32f17f4a-d16d-11ef-9809-9350156ed1ac
                        uuid_list = j['properties']['Execution_uuid'].split(",")
                        # check if user specified exec_uuid exists inside local mlmd
                        if exec_uuid in uuid_list: 
                            execution_flag = 1
                            # calling mlmd_push api to push mlmd_data = json.loads(json_payload)["Pipeline"]
                # checks if given execution present in mlmdmlmd file to cmf-server
                            response = server_interface.call_mlmd_push(
                                json_payload, url, exec_uuid, pipeline_name
                            )
                            break
                if execution_flag == 0:
                    raise ExecutionUUIDNotFound(exec_uuid)
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
                executions = query.get_all_executions_in_pipeline(pipeline_name)
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
        "--execution_uuid",
        action="append",
        help="Specify Execution uuid.",
        metavar="<exec_uuid>",
    )

    parser.add_argument(
        "-t",
        "--tensorboard",
        action="append",
        help="Specify path to tensorboard logs for the pipeline.",
        metavar="<tensorboard>"
    )

    parser.set_defaults(func=CmdMetadataPush)
