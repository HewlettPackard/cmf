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

import argparse
import os

from cmflib.cli.command import CmdBase
from cmflib import cmfquery

class CmdListArtifacts(CmdBase):
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

        df = query.get_all_artifacts_by_context(self.args.pipeline_name)
        if not df.empty:
            if self.args.artifact_id:
                try:
                    if int(self.args.artifact_id) in list(df['id']): # Converting series to list 
                        df = df.query(f'id == {int(self.args.artifact_id)}')
                    else:
                        df = "Artifact id does not exist.."
                except:
                        df = "Artifact id does not exist.."
        else:
            df = "Pipeline does not exist..."
        return df

def add_parser(subparsers, parent_parser):
    ARTIFACT_LIST_HELP = "Display list of artifacts in current cmf configuration"

    parser = subparsers.add_parser(
        "artifacts",
        parents=[parent_parser],
        description="Display artifacts",
        help=ARTIFACT_LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_argumets = parser.add_argument_group("required arguments")

    required_argumets.add_argument(
        "-p", 
        "--pipeline_name", 
        required=True,
        help="Specify pipeline name.", 
        metavar="<pipeline_name>", 
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>",
    )

    parser.add_argument(
        "-a", 
        "--artifact_id", 
        help="Specify artifact id.", 
        metavar="<artifact_id>",
    )

    parser.set_defaults(func=CmdListArtifacts)