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

from cmflib.commands.artifact import pull, push
from cmflib.cli.utils import *

SUB_COMMANDS = [pull, push]

# This parser adds positional arguments to the main parser
def add_parser(subparsers, parent_parser):
    ARTIFACT_HELP = "Command for artifact pull/push."

    artifact_parser = subparsers.add_parser(
        "artifact",
        parents=[parent_parser],
        description="Pull or Push artifacts as per current cmf configuration.",
        help=ARTIFACT_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    artifact_subparsers = artifact_parser.add_subparsers(
        dest="cmd", help="Use `cmf artifact CMD --help` for " "command-specific help."
    )

    fix_subparsers(artifact_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(artifact_subparsers, parent_parser)
