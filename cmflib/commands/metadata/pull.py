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
import json
import os
from cmflib import merger
from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdMetadataPull(CmdBase):
    def run(self):
        url = "http://127.0.0.1:80"
        directory_to_dump = ""
        data = ""
        cmd = "pull"
        mlmd_data = ""
        execution_flag = 0
        if self.args.file_name:
            directory_to_dump = self.args.file_name
        else:
            directory_to_dump = os.getcwd()
        if self.args.execution:
            output = server_interface.call_mlmd_pull(url)
            exec_id = self.args.execution
            mlmd_data = json.loads(output.content)["Pipeline"]
            for i in mlmd_data[0]["stages"]:
                for j in i["executions"]:
                    if j["id"] == int(exec_id):
                        execution_flag = 1
                        break
            if execution_flag == 0:
                print("Given execution not found in mlmd")
            else:
                merger.pull_execution_to_mlmd(
                    mlmd_json.content,
                    directory_to_dump + "/mlmd",
                    self.args.pipeline_name,
                    self.args.execution,
                )
        else:
            output = server_interface.call_mlmd_pull(url)
            mlmd_data = output.content
            merger.parse_json_to_mlmd(mlmd_data, directory_to_dump + "/mlmd", cmd)
        return 0


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pull is user-generated to fetch mlmd from server to local "

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="This is pull command",
        help=PULL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-p",
        "--pipeline_name",
        required=True,
        help="Specify Pipeline name",
        metavar="<pipeline_name>",
    )

    required_arguments.add_argument(
        "-f",
        "--file_name",
        help="Specify location to pull mlmd file",
        metavar="<file_name>",
    )

    parser.add_argument(
        "-e",
        "--execution",
        help="Get execution from execution id",
        metavar="<exec_name>",
    )

    parser.set_defaults(func=CmdMetadataPull)
