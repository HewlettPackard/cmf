import argparse

from cmflib.commands.init import minioS3, amazonS3, local, sshremote, show
from cmflib.cli.utils import *

SUB_COMMANDS = [minioS3, amazonS3, local, sshremote, show]


def add_parser(subparsers, parent_parser):
    METADATA_HELP = "Command for initializing multiple repos for CMF"

    metadata_parser = subparsers.add_parser(
        "init",
        parents=[parent_parser],
        description="This command is used to initialize multiple repos for cmf",
        help=METADATA_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    metadata_subparsers = metadata_parser.add_subparsers(
        dest="cmd",
        help="Use `cmf init CMD --help` for " "command-specific help.",
    )

    fix_subparsers(metadata_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(metadata_subparsers, parent_parser)
