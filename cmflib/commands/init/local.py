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
from cmflib.cli.utils import create_cmf_config, execute_subprocess_command


class CmdInitLocal(CmdBase):
    def run(self):
        cmf_config = "./.cmfconfig"
        output = ""
        if self.args.cmf_server_ip:
            output = create_cmf_config(cmf_config, self.args.cmf_server_ip)
        else:
            if not os.path.exists(cmf_config):
                output = create_cmf_config(cmf_config, "http://127.0.0.1:80")
        if output.find("Exception") != -1:
            return output

        # finding path of current python site_packages
        site_packages_loc = next(p for p in sys.path if f"{sys.exec_prefix}/lib" in p)
        # location of git_initialize.sh
        file = f"{site_packages_loc}/cmflib/commands/init/git_initialize.sh"

        # check whether git_initialize.sh exists
        if not os.path.exists(file):
            return "Exception occurred: Unable to initialise git."

        # executing git_initialize.sh
        result = execute_subprocess_command(
            ["sh", f"{file}", f"{self.args.git_remote_url}"]
        )
        if result.find("Exception occurred") != -1:
            return result
        if len(result) != 0:
            print(result)

        # location of dvc_script_local.sh
        file = f"{site_packages_loc}/cmflib/commands/init/dvc_script_local.sh"

        #  check whether dvc_script_local.sh exists
        if not os.path.exists(file):
            return "Exception occurred: Unable to initialise CMF."

        # executing dvc_script_local.sh
        result = execute_subprocess_command(
            [
                "sh",
                f"{file}",
                f"{self.args.path}",
            ]
        )
        if result.find("Exception occurred") != -1:
            return result
        return result


def add_parser(subparsers, parent_parser):
    HELP = "Initialises local directory as artifact repository."

    parser = subparsers.add_parser(
        "local",
        parents=[parent_parser],
        description="This command initialises local directory as CMF artifact repository.",
        help=HELP,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--path",
        required=True,
        help="Specify local directory path.",
        metavar="<path>",
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

    parser.set_defaults(func=CmdInitLocal)
