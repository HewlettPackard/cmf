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

import argparse

from cmflib.commands.metadata import push, pull, export
from cmflib.cli.utils import *

SUB_COMMANDS = [push, pull, export]

# This parser adds positional arguments to the main parser
def add_parser(subparsers, parent_parser):
    METADATA_HELP = "Command for metadata pull, push and export."

    metadata_parser = subparsers.add_parser(
        "metadata",
        parents=[parent_parser],
        description="Command pulls or pushes metadata on to cmf-server and exports the local mlmd into json.",
        help=METADATA_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    metadata_subparsers = metadata_parser.add_subparsers(
        dest="cmd", help="Use `cmf metadata CMD --help` for " "command-specific help."
    )

    fix_subparsers(metadata_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(metadata_subparsers, parent_parser)
