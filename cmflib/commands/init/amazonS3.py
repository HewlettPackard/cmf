#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex

from cmflib import cmfquery
from cmflib.cli.command import CmdBase


class CmdInitAmazonS3(CmdBase):
    def run(self):
        file = "dvc_script_amazonS3.sh"
        abs_path = None
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        subprocess.call(
            shlex.split(
                f"sh {abs_path} {self.args.url} {self.args.access_key_id} {self.args.secret_key}"
            )
        )
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Initialise amazon S3 bucket"

    parser = subparsers.add_parser(
        "amazonS3",
        parents=[parent_parser],
        description="This command is used to initialise amazon S3 bucket",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url", required=True, help="Specify url to bucket", metavar="<url>"
    )

    required_arguments.add_argument(
        "--access-key-id",
        required=True,
        help="Specify Access Key Id",
        metavar="<access_key_id>",
    )

    required_arguments.add_argument(
        "--secret-key", required=True, help="Specify Secret Key", metavar="<secret_key>"
    )

    parser.set_defaults(func=CmdInitAmazonS3)
