###
# Copyright (2024) Hewlett Packard Enterprise Development LP
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

import argparse
import os

from cmflib.cli.command import CmdBase
from cmflib import cmfquery
from cmflib.dvc_wrapper import dvc_get_config

class CmdPipelineList(CmdBase):
    def run(self):
        # Check if 'cmf' is configured.
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if len(result) == 0:
            return msg
        
        current_directory = os.getcwd()
        if not self.args.file_name:         # If self.args.file_name is None or an empty list ([]). 
            mlmd_file_name = "./mlmd"       # Default path for mlmd file name.
        elif len(self.args.file_name) > 1:  # If the user provided more than one file name. 
            return "Error: You can only provide one file name using the -f flag."
        elif not self.args.file_name[0]:    # self.args.file_name[0] is an empty string ("").  
            return "Error: Missing File name"
        else:
            mlmd_file_name = self.args.file_name[0].strip()
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
        
        current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"Error: {mlmd_file_name} doesn't exists in {current_directory} directory."

        # Creating cmfquery object.
        query = cmfquery.CmfQuery(mlmd_file_name)

        return [pipeline.name for pipeline in query._get_pipelines()]


def add_parser(subparsers, parent_parser):
    PIPELINE_LIST_HELP = "Display a list of pipeline name(s) from the available mlmd file."

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Display a list of pipeline name(s) from the available mlmd file.",
        help=PIPELINE_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "-f", 
        "--file_name", 
        action="append",
        help="Specify the absolute or relative path for the input MLMD file.",
        metavar="<file_name>",
    )

    parser.set_defaults(func=CmdPipelineList)
