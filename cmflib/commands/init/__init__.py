import argparse

from cmflib.commands.init import minioremote, amazonS3, local, sshremote
from cmflib.cli.utils import *

SUB_COMMANDS = [minioremote, amazonS3, local, sshremote]


def add_parser(subparsers, parent_parser):
    METADATA_HELP = "Command for metadata pull/push"

    metadata_parser = subparsers.add_parser(
        "init",
        parents=[parent_parser],
        description="This command is used initialize CMF for multiple repos",
        help=METADATA_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    metadata_subparsers = metadata_parser.add_subparsers(
        dest="cmd",
        help="Use `cmf metadata CMD --help` for " "command-specific help.",
    )

    fix_subparsers(metadata_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(metadata_subparsers, parent_parser)
