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
import requests

from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import git_get_repo, git_get_pull, git_get_push
from cmflib.commands.artifact.push import CmdArtifactPush
from cmflib.commands.metadata.push import CmdMetadataPush
from cmflib.cmf_exception_handling import MsgSuccess, MsgFailure


class CmdRepoPush(CmdBase):
    def branch_exists(self, repo_own: str, repo_name: str, branch_name: str) -> bool:
        """
        Check if a branch exists in a GitHub repository.

        Args:
            repo_owner: The owner of the GitHub repository.
            repo_name: The name of the GitHub repository.
            branch_name: The name of the branch to check.

        Returns:
            bool: True if the branch exists, otherwise False.
        """
        url = f"https://api.github.com/repos/{repo_own}/{repo_name}/branches/{branch_name}"
        res = requests.get(url)

        if res.status_code == 200:
            return True
        return False

    def git_push(self):
        # Getting github url from cmf init command
        url = git_get_repo()
        # Example url = https://github.com/ABC/my-repo
        url = url.split("/")
        # Check whether branch exists in git repo or not
        # url[-2] = ABC, url-1] = my-repo
        if self.branch_exists(url[-2], url[-1], "mlmd"):
            # 1. pull the code from mlmd branch
            # 2. push the code inside mlmd branch
            stdout, stderr, returncode = git_get_pull()
            if returncode != 0:
                raise MsgFailure(msg_str=f"Error pulling changes: {stderr}")
            print(stdout)
        # push the code inside mlmd branch
        stdout, stderr, returncode = git_get_push()
        if returncode != 0:
            raise MsgFailure(msg_str=f"Error pushing changes: {stderr}")
        return MsgSuccess(msg_str="Successfully pushed and pulled changes!")
        

    def run(self):
        print("Executing cmf artifact push command..")
        artifact_push_instance = CmdArtifactPush(self.args)
        if artifact_push_instance.run().status == "success":
            print("Executing cmf metadata push command..")
            metadata_push_instance = CmdMetadataPush(self.args)
            if metadata_push_instance.run().status == "success":
                print("Execution git push command..")
                return self.git_push()
         

def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Push artifacts, metadata files, and source code to the user's artifact repository, cmf-server, and git respectively."

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push artifacts, metadata files, and source code to the user's artifact repository, cmf-server, and git respectively.",
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
        action="append",
        help="Specify Execution id.",
        default=None,
        metavar="<exec_id>",
    )

    parser.add_argument(
        "-t",
        "--tensorboard",
        action="append",
        help="Specify path to tensorboard logs for the pipeline.",
        metavar="<tensorboard>"
    )

    parser.set_defaults(func=CmdRepoPush)
