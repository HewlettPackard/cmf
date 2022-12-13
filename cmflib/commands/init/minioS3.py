#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex

from cmflib.cli.command import CmdBase
from cmflib.cli.utils import create_cmf_config


class CmdInitMinioS3(CmdBase):
    def run(self):
        cmf_config = "./.cmfconfig"
        if "self.args.cmf_server_ip" in globals():
            create_cmf_config(cmf_config, self.args.cmf_server_ip)
        else:
            if not os.path.exists(cmf_config):
                create_cmf_config(cmf_config, "http://127.0.0.1:80")
        abs_path = None
        file = "git_initialize.sh"
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        result = subprocess.run(
            ["sh", f"{abs_path}", f"{self.args.git_remote_url}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
        file = "dvc_script_minio.sh"
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        result = subprocess.run(
            [
                "sh",
                f"{abs_path}",
                f"{self.args.url}",
                f"{self.args.endpoint_url}",
                f"{self.args.access_key_id}",
                f"{self.args.secret_key}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.stdout


def add_parser(subparsers, parent_parser):
    HELP = "Initialize minio S3 bucket"

    parser = subparsers.add_parser(
        "minioS3",
        parents=[parent_parser],
        description="This command is to initialize minio S3 bucket",
        help=HELP,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--url",
        required=True,
        help="Specify url to bucket",
        metavar="<url>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--endpoint-url",
        required=True,
        help="Specify endpoint url which is used to access minio locally/remotely running UI",
        metavar="<endpoint_url>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--access-key-id",
        required=True,
        help="Specify Access Key Id",
        metavar="<access_key_id>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--secret-key",
        required=True,
        help="Specify Secret Key",
        metavar="<secret_key>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--git-remote-url",
        required=True,
        help="Url to git repo",
        metavar="<git_remote_url>",
        default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--cmf-server-IP",
        help="Specify Cmf Server IP",
        metavar="<cmf_server_ip>",
        default="http://127.0.0.1:80",
    )

    parser.set_defaults(func=CmdInitMinioS3)
