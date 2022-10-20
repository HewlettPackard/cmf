import argparse

from cmflib.commands.metadata import push
from cmflib.cli.utils import *

SUB_COMMANDS = [
    push
]


def add_parser(subparsers, parent_parser):
    METADATA_HELP = "Command for metadata pull/push"

    metadata_parser = subparsers.add_parser(
        "metadata",
        parents=[parent_parser],
        description="This command is used pull/push metadata",
        help=METADATA_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    metadata_subparsers = metadata_parser.add_subparsers(
        dest="cmd",
        help="Use `cmf metadata CMD --help` for " "command-specific help.",
    )

    fix_subparsers(metadata_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(metadata_subparsers, parent_parser)
