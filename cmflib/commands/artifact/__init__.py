import argparse

from cmflib.commands.artifact import pull, push
from cmflib.cli.utils import *

SUB_COMMANDS = [pull, push]


def add_parser(subparsers, parent_parser):
    ARTIFACT_HELP = "Command for artifact pull/push"

    artifact_parser = subparsers.add_parser(
        "artifact",
        parents=[parent_parser],
        description="This command is used pull/push Artifact",
        help=ARTIFACT_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    artifact_subparsers = artifact_parser.add_subparsers(
        dest="cmd",
        help="Use `cmf artifact CMD --help` for " "command-specific help.",
    )

    fix_subparsers(artifact_subparsers)
    for cmd in SUB_COMMANDS:
        cmd.add_parser(artifact_subparsers, parent_parser)
