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

from cmflib.cli.command import CmdBase
from cmflib.utils.cmf_config import CmfConfig
from cmflib.cmf_exception_handling import CmfInitShow
from cmflib.utils.helper_functions import fetch_cmf_config_path

class CmdInitShow(CmdBase):
    def run(self, live):
        output, config_file_path = fetch_cmf_config_path()
        attr_dict = CmfConfig.read_config(config_file_path)
        # Combine the two dictionaries
        combined_dict = output | attr_dict
        attr_list = []
        for key, value in combined_dict.items():
            temp_str = f"{key} = {value}"
            attr_list.append(temp_str)
        attr_str = "\n".join(attr_list)
        return CmfInitShow(attr_str)


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
