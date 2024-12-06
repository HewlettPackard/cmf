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

import argparse

from cmflib.commands.execution import list
from cmflib.cli.utils import *

SUB_COMMANDS = [list]

# This parser adds positional argumets to the main parser
def add_parser(subparsers, parent_parser):
    LIST_HELP = "Display all executions with detailed information from the specified MLMD file."

    list_parser = subparsers.add_parser(
        "execution", 
        parents=[parent_parser],
        description="Display all executions with detailed information from the specified MLMD file.",
        help=LIST_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    list_subparsers = list_parser.add_subparsers(
        dest="cmd", help="Use `cmf execution CMD --help` for " "command-specific help."
    )

    fix_subparsers(list_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(list_subparsers, parent_parser)

