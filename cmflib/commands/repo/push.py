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
from cmflib import cmfquery
from cmflib.dvc_wrapper import dvc_get_config, git_get_repo, git_checkout_new_branch
from cmflib.commands.artifact.push import CmdArtifactPush
from cmflib.commands.metadata.push import CmdMetadataPush


class CmdRepoPush(CmdBase):
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

    def git_push(self):
        url = git_get_repo()
        url = url.split("/")
        # whether branch exists in git repo or not
        if self.branch_exists(url[-2], url[-1], "mlmd"):
            # print("branch exists")
            # pull the code
            # push the code
            stdout, stderr, returncode = self.run_command("git pull cmf_origin mlmd")
            # print(returncode+"1")
            if returncode != 0:
                return f"Error pulling changes: {stderr}"
            print(stdout)
    
            stdout, stderr, returncode = self.run_command("git push -u cmf_origin mlmd")
            if returncode != 0:
                return f"Error pushing changes: {stderr}"
            print(stdout)
            return "Successfully pushed and pulled changes!"
        else:
            print("branch not exists")
            # push the code
            stdout, stderr, returncode = self.run_command("git push -u cmf_origin mlmd")
            if returncode != 0:
                return f"Error pushing changes: {stderr}"
            return "Successfully pushed and pulled changes!"
        

    def run(self):
        # # check whether dvc is configured or not
        # msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        # result = dvc_get_config()
        # if len(result) == 0:
        #     return msg
    
        # current_directory = os.getcwd()
        # mlmd_file_name = "./mlmd"

        # # check whether mlmd file exists or not
        # if self.args.file_name:
        #     mlmd_file_name = self.args.file_name
        #     current_directory = os.path.dirname(self.args.file_name)

        # # checks if mlmd file is present in current directory or given directory
        # if not os.path.exists(mlmd_file_name):
        #     return f"ERROR: {mlmd_file_name} doesn't exists in the {current_directory}."
        # else:
        #     # creating cmfquery object
        #     query = cmfquery.CmfQuery(mlmd_file_name)
        #     # Put a check to see whether pipline exists or not
        #     pipeline_name = self.args.pipeline_name
        #     if not query.get_pipeline_id(pipeline_name) > 0:
        #         return f"ERROR: Pipeline {pipeline_name} doesn't exist!!"
            
            print("Executing cmf artifact push command..")
            artifact_push_instance = CmdArtifactPush(self.args)
            # print(artifact_push_instance.run().status)
            if artifact_push_instance.run().status == "success":
                print("Executing cmf metadata push command..")
                metadata_push_instance = CmdMetadataPush(self.args)
                if metadata_push_instance.run().status == "success":
                    print("Execution git push command..")
                    print(self.git_push())
                    return self.git_push()
         

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
        "--execution",
        help="Specify Execution id.",
        default=None,
        metavar="<exec_id>",
    )

    parser.add_argument(
        "-t",
        "--tensorboard",\
        help="Specify path to tensorboard logs for the pipeline.",
        metavar="<tensorboard>"
    )

    parser.set_defaults(func=CmdRepoPush)
