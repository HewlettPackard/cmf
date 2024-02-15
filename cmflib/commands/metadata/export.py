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
from cmflib import cmfquery
from cmflib.cli.command import CmdBase


# This class export local mlmd data to a json file
class CmdMetadataExport(CmdBase):
    def run(self):

        current_directory = os.getcwd()
        full_path_to_dump = ""
        data = ""
        mlmd_data = ""

        mlmd_file_name = "./mlmd"

        # checks if mlmd filepath is given
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            current_directory = os.path.dirname(self.args.file_name)

        # checks if mlmd file is present in current directory or given directory
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in the {current_directory}."


        # setting directory where mlmd file will be dumped
        if self.args.json_file_name:
            if not os.path.isdir(self.args.json_file_name):
                temp = os.path.dirname(self.args.json_file_name)
                if temp != "":
                    current_directory = temp
                if os.path.exists(current_directory):
                    full_path_to_dump  = self.args.json_file_name
                else:
                    return f"{current_directory} doesn't exists."
            else:
                return "Provide path with file name."
        else:
            full_path_to_dump = os.getcwd() + f"/{self.args.pipeline_name}.json"

        # initialising cmfquery class
        query = cmfquery.CmfQuery(mlmd_file_name)

        # check if pipeline exists in mlmd 
        pipeline = query.get_pipeline_id(self.args.pipeline_name)

        if pipeline > 0:
            # pulling data from local mlmd file
            json_payload = query.dumptojson(self.args.pipeline_name,None)

            # write metadata into json file
            with open(full_path_to_dump, 'w') as f:
                f.write(json.dumps(json.loads(json_payload),indent=2))
                return f"SUCCESS: metadata successfully exported in {full_path_to_dump}."
        else:
            return f"{self.args.pipeline_name} doesn't exists in {mlmd_file_name}!!"


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Exports local mlmd's metadata to a json file."

    parser = subparsers.add_parser(
        "export",
        parents=[parent_parser],
        description="Export local mlmd's metadata in json format to a json file.",
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

    parser.add_argument(
        "-j",
        "--json_file_name",
        help="Specify json file name with full path.",
        metavar="<json_file_name>",
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>"
    )

    parser.set_defaults(func=CmdMetadataExport)
