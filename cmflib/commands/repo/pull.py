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

from cmflib.cli.command import CmdBase
from cmflib.utils.helper_functions import branch_exists
from cmflib.commands.artifact.pull import CmdArtifactPull
from cmflib.commands.metadata.pull import CmdMetadataPull
from cmflib.cmf_exception_handling import MsgSuccess, MsgFailure
from cmflib.dvc_wrapper import git_get_repo, git_get_pull, git_get_branch


class CmdRepoPull(CmdBase):
    def git_pull(self):
        # Getting GitHub URL from cmf init command
        url = git_get_repo()
        # Example url = https://github.com/ABC/my-repo OR https://github.com/ABC/my-repo.git
        # Check if the URL is a GitHub URL
        if "github.com" not in url:
            raise MsgFailure(msg_str="The repository URL is not a GitHub URL.")
        
        # Extracting the repository owner and name from the URL
        # repo_owner = ABC, repo_name = my-repo
        url_parts = url.split("/")
        repo_owner = url_parts[-2]
        repo_name = url_parts[-1].split(".")[0]
        
        # Getting the current branch name
        branch_name = git_get_branch()[0]
        
        # Check whether the branch exists in the GitHub repository
        if branch_exists(repo_owner, repo_name, branch_name):
            # pull the code from mlmd branch
            print("git pull started...")
            stdout, stderr, returncode = git_get_pull(branch_name)
            if returncode != 0:
                raise MsgFailure(msg_str=f"{stderr}")
            return MsgSuccess(msg_str=stdout)
        else:
            raise MsgFailure(msg_str=f"{branch_name} inside {url} does not exist!!")
        
    def run(self, live):
        print("Executing cmf metadata pull command..")
        metadata_pull_instance = CmdMetadataPull(self.args)
        metadata_pull_result = metadata_pull_instance.run(live)
        if metadata_pull_result.status == "success":  
            print(metadata_pull_result.handle())          # Print the message returned by the handle() method of the metadata_pull_result object.
            print("Executing cmf artifact pull command..")
            artifact_pull_instance = CmdArtifactPull(self.args)
            artifact_pull_result = artifact_pull_instance.run(live)
            if artifact_pull_result.status == "success":
                print(artifact_pull_result.handle())   # Print the message returned by the handle() method of the artifact_pull_result object.
                print("Executing git pull command..")
                live.stop()
                return self.git_pull()


def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pull artifacts, metadata files, and source code from the user's artifact repository, cmf-server, and git respectively."

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="Pull artifacts, metadata files, and source code from the user's artifact repository, cmf-server, and git respectively.",
        help=PULL_HELP,
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
        help="Specify output metadata file name.", 
        metavar="<file_name>",
    )

    parser.add_argument(
        "-e",
        "--execution_uuid",
        action="append",
        help="Specify Execution uuid.",
        metavar="<exec_uuid>",
    )

    # The 'artifact_name' parameter is used inside 'cmf artifact pull' command.
    # To avoid errors, it is defined here with a default value of 'None' and hidden from the help text using 'argparse.SUPPRESS'.
    parser.add_argument(
        "-a", 
        "--artifact_name", 
        action="store_const",
        const="None",
        help=argparse.SUPPRESS, 
        metavar="<artifact_name>",
    )

    parser.set_defaults(func=CmdRepoPull)
