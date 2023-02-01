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
import os
import subprocess
import sys

from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import git_quiet_init, git_checkout_new_branch, git_initial_commit, git_add_remote, check_git_repo, dvc_quiet_init,\
  dvc_add_remote_repo, dvc_add_attribute
from cmflib.cli.utils import create_cmf_config


class CmdInitSSHRemote(CmdBase):
    def run(self):
        cmf_config = os.environ.get("CONFIG_FILE",".cmfconfig")
        output = ""
        if self.args.cmf_server_ip:
            output = create_cmf_config(cmf_config, self.args.cmf_server_ip)
        else:
            if not os.path.exists(cmf_config):
                output = create_cmf_config(cmf_config, "http://127.0.0.1:80")
        if output.find("Exception") != -1:
            return output

        output = check_git_repo()
        if not output:
            branch_name = "master"
            print("Starting git init.")
            git_quiet_init()
            git_checkout_new_branch(branch_name)
            git_initial_commit()
            git_add_remote(self.args.git_remote_url)
            print("git init complete.")

        print("Starting cmf init.")
        repo_type = 'sshremote'
        dvc_quiet_init()
        output = dvc_add_remote_repo(repo_type, self.args.path)
        if not output:
            return "cmf init failed."
        print(output)
        dvc_add_attribute(repo_type, 'user', self.args.user)
        dvc_add_attribute(repo_type, 'password', self.args.password)
        dvc_add_attribute(repo_type, 'port', self.args.port)
        return "cmf init complete."

def add_parser(subparsers, parent_parser):
    HELP = "Initialises remote SSH directory as artifact repository."

    parser = subparsers.add_parser(
        "sshremote",
        parents=[parent_parser],
        description="This command initialises remote SSH directory as artifact repository for CMF.",
        help=HELP,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--path",
        required=True,
        help="Specify remote ssh directory path.",
        metavar="<path>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--user",
        required=True,
        help="Specify username.",
        metavar="<user>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--port",
        required=True,
        help="Specify port.",
        metavar="<port>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--password",
        required=True,
        help="Specify password. This will be saved only on local",
        metavar="<password>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--git-remote-url",
        required=True,
        help="Specify git repo url.",
        metavar="<git_remote_url>",
        default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--cmf-server-ip",
        help="Specify cmf-server IP.",
        metavar="<cmf_server_ip>",
        default="http://127.0.0.1:80",
    )

    parser.set_defaults(func=CmdInitSSHRemote)
