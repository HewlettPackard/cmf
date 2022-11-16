#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex


from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdInitLocal(CmdBase):
    def run(self):
        file = "dvc_script_local.sh"
        abs_path = None
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        subprocess.call(
            shlex.split(
                f"sh {abs_path} {self.args.url}"
            )
        )
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
