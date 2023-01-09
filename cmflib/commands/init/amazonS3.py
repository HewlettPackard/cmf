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
import shlex
import sys

from cmflib.cli.command import CmdBase
from cmflib.cli.utils import create_cmf_config


class CmdInitAmazonS3(CmdBase):
    def run(self):
        cmf_config = "./.cmfconfig"
        if self.args.cmf_server_ip:
            create_cmf_config(cmf_config, self.args.cmf_server_ip)
        else:
            if not os.path.exists(cmf_config):
                create_cmf_config(cmf_config, "http://127.0.0.1:80")

        # finding path of current python site_packages
        site_packages_loc = next(p for p in sys.path if f"{sys.exec_prefix}/lib" in p)
        # location of git_initialize.sh
        file = f"{site_packages_loc}/cmflib/commands/init/git_initialize.sh"

        # executing git_initialize.sh
        result = subprocess.run(
            ["sh", f"{file}", f"{self.args.git_remote_url}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.stdout:
            print(result.stdout)

        # location of dvc_script_amazonS3.sh
        file = f"{site_packages_loc}/cmflib/commands/init/dvc_script_amazonS3.sh"

        # executing dvc_script_amazonS3.sh
        result = subprocess.run(
            [
                "sh",
                f"{file}",
                f"{self.args.url}",
                f"{self.args.access_key_id}",
                f"{self.args.secret_key}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.stdout


def add_parser(subparsers, parent_parser):
    HELP = "Initialises Amazon S3 as artifact repository."

    parser = subparsers.add_parser(
        "amazonS3",
        parents=[parent_parser],
        description="This command initialises Amazon S3 bucket as artifact repository for CMF.",
        help=HELP,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url",
        required=True,
        help="Specify Amazon S3 bucket url.",
        metavar="<url>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--access-key-id",
        required=True,
        help="Specify Access Key Id.",
        metavar="<access_key_id>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--secret-key",
        required=True,
        help="Specify Secret Key.",
        metavar="<secret_key>",
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

    parser.set_defaults(func=CmdInitAmazonS3)
