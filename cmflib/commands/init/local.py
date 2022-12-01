#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex


from cmflib import cmfquery
from cmflib.cli.command import CmdBase


class CmdInitLocal(CmdBase):
    def run(self):
        abs_path = None
        file = "git_initialize.sh"
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        subprocess.call(
            shlex.split(f"sh {abs_path} {self.args.git_remote_url}")
        )
        file = "dvc_script_local.sh"
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        subprocess.call(
            shlex.split(f"sh {abs_path} {self.args.url}")
        )
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Initialise local bucket"

    parser = subparsers.add_parser(
        "local",
        parents=[parent_parser],
        description="This command is used to initialise local bucket",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url", required=True, help="Specify url to bucket", metavar="<url>"
    )

    required_arguments.add_argument(
        "--git-remote-url",
        required=True,
        help="Url to git repo",
        metavar="<git_remote_url>",
    )

    parser.set_defaults(func=CmdInitLocal)
