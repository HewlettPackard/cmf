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


# This class pushes mlmd file to cmf-server
class CmdMetadataPush(CmdBase):
    def run(self):
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"

        # checks if mlmd filepath is given
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            current_directory = os.path.dirname(self.args.file_name)

        # checks if mlmd file is present in current directory or given directory
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in the {current_directory}."

        query = cmfquery.CmfQuery(mlmd_file_name)
        # print(json.dumps(json.loads(json_payload), indent=4, sort_keys=True))
        execution_flag = 0
        status_code = 0

        # Get url from config
        cmfconfig = os.environ.get("CONFIG_FILE",".cmfconfig")

        # find root_dir of .cmfconfig
        output = find_root(cmfconfig)

        # in case, there is no .cmfconfig file
        if output.find("'cmf' is  not configured") != -1:
            return output

        config_file_path = os.path.join(output, cmfconfig)
        attr_dict = CmfConfig.read_config(config_file_path)
        url = attr_dict.get("cmf-server-ip", "http://127.0.0.1:80")

        print("metadata push started")
        print("........................................")

        if self.args.pipeline_name in query.get_pipeline_names():  # Checks if pipeline name exists
            json_payload = query.dumptojson(
                self.args.pipeline_name,None
            )  # converts mlmd file to json format
            if self.args.execution:  # checks if execution_id is given by user
                exec_id = self.args.execution
                mlmd_data = json.loads(json_payload)["Pipeline"]
                for i in mlmd_data[0][
                    "stages"
                ]:  # checks if given execution_id present in mlmd
                    for j in i["executions"]:
                        if j["id"] == int(exec_id):
                            execution_flag = 1
                            # calling mlmd_push api to push mlmd file to cmf-server
                            response = server_interface.call_mlmd_push(
                                json_payload, url, exec_id
                            )
                            break
                if execution_flag == 0:
                    return "Given execution is not found in mlmd."
            else:
                exec_id = None
                response = server_interface.call_mlmd_push(json_payload, url, exec_id)
            status_code = response.status_code
            if status_code == 200 and response.json()['status']=="success":
                return "mlmd is successfully pushed."
            elif status_code==200 and response.json()["status"]=="exists":
                return "Executions already exists."
            elif status_code==200 and response.json()["status"]=="version_update":
                return "You need to update cmf to the latest version."
            elif status_code == 404:
                return "ERROR: cmf-server is not available."
            elif status_code == 500:
                return "ERROR: Internal server error."
            else:
                return "ERROR: Status Code = {status_code}. Unable to push mlmd."
        else:
            return "Pipeline name " + self.args.pipeline_name + " doesn't exists."


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

    parser.set_defaults(func=CmdMetadataPush)
