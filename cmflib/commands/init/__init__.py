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

from cmflib.commands.init import minioS3, amazonS3, local, sshremote, osdfremote, show
from cmflib.cli.utils import *

SUB_COMMANDS = [minioS3, amazonS3, local, sshremote, osdfremote, show]

# This parser adds positional arguments to the main parser
def add_parser(subparsers, parent_parser):
    METADATA_HELP = "Command for initializing different artifact repositories for CMF."

    metadata_parser = subparsers.add_parser(
        "init",
        parents=[parent_parser],
        description="This command initializes different artifact repositories for CMF.",
        help=METADATA_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    metadata_subparsers = metadata_parser.add_subparsers(
        dest="cmd", help="Use `cmf init CMD --help` for " "command-specific help."
    )

    fix_subparsers(metadata_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(metadata_subparsers, parent_parser)
