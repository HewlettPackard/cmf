###
# Copyright (2025) Hewlett Packard Enterprise Development LP
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

from cmflib.commands.recorder import start
from cmflib.cli.utils import *

SUB_COMMANDS = [start]

# This parser adds positional arguments to the main parser
def add_parser(subparsers, parent_parser):
    RECORDER_HELP = "Records agent session traces into CMF as Dataset artifacts."

    recorder_parser = subparsers.add_parser(
        "recorder",
        parents=[parent_parser],
        description="Records agent session traces (from opencode-capture or any "
                    "trace-event producer) into CMF as Dataset artifacts under "
                    "an AgentTurn stage.",
        help=RECORDER_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    recorder_subparser = recorder_parser.add_subparsers(
        dest="cmd", help="Use `cmf recorder CMD --help` for " "command-specific help."
    )

    fix_subparsers(recorder_subparser)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(recorder_subparser, parent_parser)
