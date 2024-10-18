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

#!/usr/bin/env python3
import argparse
import os
import subprocess
import requests

from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import dvc_get_config, git_get_repo, git_checkout_new_branch
from cmflib.commands.artifact.pull import CmdArtifactPull
from cmflib.commands.metadata.pull import CmdMetadataPull


class CmdRepoPush(CmdBase):
    def __init__(self, args):
        self.args = args
    
    def run_command(self, command, cwd=None):
        process = subprocess.Popen(command, cwd=cwd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return (stdout.decode('utf-8').strip() if stdout else '',
                stderr.decode('utf-8').strip() if stderr else '',
                process.returncode)
    
    def branch_exists(self, repo_own, repo_name, branch_name):
        url = f"https://api.github.com/repos/{repo_own}/{repo_name}/branches/{branch_name}"
        res = requests.get(url)

        if res.status_code == 200:
            return True
        return False


    def run(self):
        # check whether dvc is configured or not
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if len(result) == 0:
            return msg
        
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            if mlmd_file_name == "mlmd":
                mlmd_file_name = "./mlmd"
            current_directory = os.path.dirname(mlmd_file_name)
        if not os.path.exists(mlmd_file_name):
            return f"ERROR: {mlmd_file_name} doesn't exists in {current_directory} directory."
    
        # artifcat pull
        print("artifact pull started...")
        instance_of_artifact = CmdArtifactPull(self.args)
        instance_of_artifact.run()

        # metadata pull
        print("metadata pull started...")
        instance_of_metadata = CmdMetadataPull(self.args)
        instance_of_metadata.run()

        url = git_get_repo()
        url = url.split("/")
        # whether branch exists in git repo or not
        if self.branch_exists(url[-2], url[-1], "mlmd"):
            print("branch exists")
            # git pull
            print("git pull started...")
            stdout, stderr, returncode = self.run_command("git pull cmf_origin mlmd")
            # print(returncode+"1")
            print(stdout)
            if returncode != 0:
                return f"Error pulling changes: {stderr}"
            return stdout
        else:
            return "mlmd branch is not exists in github..."

def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Pull user-generated mlmd to server to create one single mlmd file for all the pipelines."

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="Pull user's mlmd to cmf-server.",
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
        "-a", "--artifact_name", help="Specify artifact name.", metavar="<artifact_name>"
    )

    parser.set_defaults(func=CmdRepoPush)
