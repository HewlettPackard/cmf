#!/usr/bin/env python3
import argparse
import os

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdInitSSHRemote(CmdBase):
    def run(self):
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Used to initialise ssh remote bucket"

    parser = subparsers.add_parser(
        "sshremote",
        parents=[parent_parser],
        description="This is command is used to initialise ssh remote bucket",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url", required=True, help="Specify url to bucket", metavar="<url>"
    )

    required_arguments.add_argument(
        "--user",
        required=True,
        help="Specify user",
        metavar="<user>",
    )

    required_arguments.add_argument(
        "--port", required=True, help="Specify Port", metavar="<port>"
    )

    required_arguments.add_argument(
        "--password",
        required=True,
        help="Specify password. This will be saved only on local",
        metavar="<password>",
    )

    parser.set_defaults(func=CmdInitSSHRemote)
