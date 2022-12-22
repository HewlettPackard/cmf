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
import os
import subprocess
import shlex

from cmflib.cli.command import CmdBase
from cmflib.cli.utils import create_cmf_config


class CmdInitSSHRemote(CmdBase):
    def run(self):
        cmf_config = "./.cmfconfig"
        if self.args.cmf_server_ip:
            create_cmf_config(cmf_config, self.args.cmf_server_ip)
        else:
            if not os.path.exists(cmf_config):
                create_cmf_config(cmf_config, "http://127.0.0.1:80")
        abs_path = None
        file = "git_initialize.sh"
        # finding absolute path for git_initialize.sh
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        # executing git_initialize.sh
        result = subprocess.run(
            ["sh", f"{abs_path}", f"{self.args.git_remote_url}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        file = "dvc_script_sshremote.sh"
        # finding absolute path for dvc_script_sshremote.sh
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        # executing dvc_script_sshremote.sh
        result = subprocess.run(
            [
                "sh",
                f"{abs_path}",
                f"{self.args.path}",
                f"{self.args.user}",
                f"{self.args.port}",
                f"{self.args.password}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.stdout


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
