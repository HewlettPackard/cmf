#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex

from cmflib import cmfquery
from cmflib.cli.command import CmdBase


class CmdInitSSHRemote(CmdBase):
    def run(self):
        file = "dvc_script_sshremote.sh"
        abs_path = None
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        subprocess.call(
            shlex.split(
                f"sh {abs_path} {self.args.url} {self.args.user} {self.args.port} {self.args.password}"
            )
        )
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Initialise ssh remote bucket"

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
