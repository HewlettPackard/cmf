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
import json
import os
from cmflib import merger
from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.cli.utils import read_cmf_config, find_root
from cmflib.request_mlmdserver import server_interface

# This class pulls mlmd file from cmf-server
class CmdMetadataPull(CmdBase):
    def run(self):
        config_file = ".cmfconfig"
        url = "http://127.0.0.1:80"
        if os.path.exists(find_root(config_file)):
            url = read_cmf_config(
                os.path.join(find_root(config_file), config_file)
            ).split("=")[1]
        directory_to_dump = ""
        data = ""
        cmd = "pull"
        mlmd_data = ""
        status = 0
        execution_flag = 0
        if self.args.file_path:  # setting directory where mlmd file will be dumped
            directory_to_dump = self.args.file_path
        else:
            directory_to_dump = os.getcwd()
        output = server_interface.call_mlmd_pull(
            url, self.args.pipeline_name
        )  # calls cmf-server api to get mlmd file data(Json format)
        status = output.status_code
        # checks If given pipeline does not exists/ elif pull mlmd file/ else mlmd file is not available
        if output.content.decode() == "NULL":
            return "Pipeline name " + self.args.pipeline_name + " doesn't exist"
        elif output.content:
            if self.args.execution:  # checks if execution_id given by user
                exec_id = self.args.execution
                mlmd_data = json.loads(output.content)["Pipeline"]
                for i in mlmd_data[0][
                    "stages"
                ]:  # checks if given execution_id present in mlmd
                    for j in i["executions"]:
                        if j["id"] == int(exec_id):
                            execution_flag = 1
                            break
                if execution_flag == 0:
                    print("Given execution id is not available in mlmd.")
                else:
                    try:
                        merger.pull_execution_to_mlmd(  # converts mlmd json data to mlmd file for given execution_id
                            output.content,
                            directory_to_dump + "/mlmd",
                            self.args.pipeline_name,
                            self.args.execution,
                        )
                    except Exception as e:
                        return e
            else:
                mlmd_data = output.content
                try:
                    merger.parse_json_to_mlmd(
                        mlmd_data, directory_to_dump + "/mlmd", cmd
                    )  # converts mlmd json data to mlmd file
                except Exception as e:
                    return e
            # verifying status codes
            if status == 200:
                return "SUCCESS: mlmd is successfully pulled."
            elif status == 404:
                return "ERROR: cmf-server is not available."
            elif status == 500:
                return "ERROR: Internal server error."
            else:
                return "ERROR: Unable to pull mlmd."
        else:
            return "mlmd file not available on cmf-server."


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
        help="Specify Pipeline name.",
        metavar="<pipeline_name>",
    )

    required_arguments.add_argument(
        "-f",
        "--file_path",
        help="Specify location to pull mlmd file.",
        metavar="<file_path>",
    )

    parser.add_argument(
        "-e",
        "--execution",
        help="Specify Execution id",
        metavar="<exec_id>",
    )

    parser.set_defaults(func=CmdMetadataPull)
