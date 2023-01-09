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

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.cli.utils import read_cmf_config, find_root


class CmdInitShow(CmdBase):
    def run(self):
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = subprocess.run(
            ["dvc", "config", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if len(result.stdout) == 0:
            return msg
        else:
            cmf_config_root = find_root(".cmfconfig")
            if not os.path.exists(cmf_config_root):
                return cmf_config_root
            config_file_path = os.path.join(cmf_config_root, ".cmfconfig")
            server_ip = read_cmf_config(config_file_path)
            return f"{result.stdout}{server_ip}"


def add_parser(subparsers, parent_parser):
    HELP = "Show current CMF configuration."

    parser = subparsers.add_parser(
        "show",
        parents=[parent_parser],
        description="This command shows current cmf configuration including cmf server ip.",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.set_defaults(func=CmdInitShow)
