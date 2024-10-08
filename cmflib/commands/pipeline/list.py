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

class CmdPipelineList(CmdBase):
    def run(self):
        current_directory = os.getcwd()
        # default path for mlmd file name
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."

        # Creating cmfquery object
        query = cmfquery.CmfQuery(mlmd_file_name)

        return [pipeline.name for pipeline in query._get_pipelines()]

def add_parser(subparsers, parent_parser):
    PIPELINE_LIST_HELP = "Display list of pipelines in current cmf configuration"

    parser = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        description="Display pipeline list",
        help=PIPELINE_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>",
    )

    parser.set_defaults(func=CmdPipelineList)
