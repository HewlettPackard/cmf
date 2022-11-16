#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdInitMinioRemote(CmdBase):
    def run(self):
        file = "dvc_script_module.sh"
        abs_path = None
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        print(abs_path)
        subprocess.call(
            shlex.split(
                f"sh dvc_script_minio.sh {self.args.url} {self.args.endpoint_url} {self.args.access_key_id} {self.args.secret_key}"
            )
        )
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "This is command is to initialize minio S3 bucket"

    parser = subparsers.add_parser(
        "minioremote",
        parents=[parent_parser],
        description="This is command is to initialize minio S3 bucket",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url", required=True, help="Specify url to bucket", metavar="<url>"
    )

    required_arguments.add_argument(
        "--endpoint-url",
        required=True,
        help="Specify endpoint url which is used to access minio locally/remotely running UI",
        metavar="<endpoint_url>",
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

    parser.set_defaults(func=CmdInitMinioRemote)
