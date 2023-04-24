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

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.cli.utils import find_root
from cmflib.dvc_wrapper import dvc_get_config
from cmflib.utils.cmf_config import CmfConfig

class CmdInitShow(CmdBase):
    def run(self):
        cmfconfig = os.environ.get("CONFIG_FILE",".cmfconfig")
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if len(result) == 0:
            return msg
        else:
            cmf_config_root = find_root(cmfconfig)
            if cmf_config_root.find("'cmf' is not configured") != -1:
                return msg
            config_file_path = os.path.join(cmf_config_root, cmfconfig)
            attr_dict = CmfConfig.read_config(config_file_path)
            attr_list = []
            for key, value in attr_dict.items():
                temp_str = f"{key} = {value}"
                attr_list.append(temp_str)
            attr_str = "\n".join(attr_list)
            return f"{result}\n{attr_str}"


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
