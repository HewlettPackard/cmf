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

"""Main parser for the cmf cli"""
import argparse
import logging
import os
import sys

from cmflib.commands import artifact, metadata, init

from cmflib.cli import CmfParserError

COMMANDS = [artifact, metadata, init]


def _find_parser(parser, cmd_cls):
    defaults = parser._defaults  # pylint: disable=protected-access
    if not cmd_cls or cmd_cls == defaults.get("func"):
        parser.print_help()
        raise CmfParserError

    actions = parser._actions  # pylint: disable=protected-access
    for action in actions:
        if not isinstance(action.choices, dict):
            # NOTE: we are only interested in subparsers
            continue
        for subparser in action.choices.values():
            _find_parser(subparser, cmd_cls)


class CmfParser(argparse.ArgumentParser):
    """Custom parser class for cmf CLI"""

    def error(self, message, cmd_cls=None):
        _find_parser(self, cmd_cls)

    def parse_args(self, args=None, namespace=None):
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            msg = "unrecognized arguments: %s"
            self.error(msg % " ".join(argv), getattr(args, "func", None))
        return args


def get_parent_parser():
    """Create instances of a parser containing common arguments shared among
    all the commands.
    """
    parent_parser = argparse.ArgumentParser(add_help=False)
    return parent_parser


def get_main_parser():
    parent_parser = get_parent_parser()

    # Main parser
    desc = "Common Metadata Framework"
    parser = CmfParser(
        prog="cmf",
        description=desc,
        parents=[parent_parser],
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit.",
    )

    # Sub commands
    subparsers = parser.add_subparsers(
        # required= True,
        title="Available Commands",
        metavar="COMMAND",
        dest="cmd",
        help="Use `cmf COMMAND --help` for command-specific help.",
    )

    from .utils import fix_subparsers

    fix_subparsers(subparsers)

    for cmd in COMMANDS:
        cmd.add_parser(subparsers, parent_parser)

    return parser
