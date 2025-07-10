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

from cmflib.commands.dvc import ingest
from cmflib.cli.utils import *

SUB_COMMANDS = [ingest]

# This parser adds positional arguments to the main parser
def add_parser(subparsers, parent_parser):
    DVC_HELP = "Ingests metadata from the dvc.lock file into CMF."

    dvc_parser = subparsers.add_parser(
        "dvc",
        parents=[parent_parser],
        description="Ingests metadata from the dvc.lock file into the CMF.",
        help=DVC_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    dvc_subparser = dvc_parser.add_subparsers(
        dest="cmd", help="Use `cmf dvc CMD --help` for " "command-specific help."
    )

    fix_subparsers(dvc_subparser)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(dvc_subparser, parent_parser)

