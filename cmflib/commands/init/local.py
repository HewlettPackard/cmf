#!/usr/bin/env python3
import argparse
import os

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdInitLocal(CmdBase):
    def run(self):
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Used to initialise local bucket"

    parser = subparsers.add_parser(
        "local",
        parents=[parent_parser],
        description="This is command is used to initialise local bucket",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url", required=True, help="Specify url to bucket", metavar="<url>"
    )

    parser.set_defaults(func=CmdInitLocal)
