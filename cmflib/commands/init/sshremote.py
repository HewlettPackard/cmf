#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex

from cmflib import cmfquery
from cmflib.cli.command import CmdBase


class CmdInitSSHRemote(CmdBase):
    def run(self):
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
        file = "dvc_script_sshremote.sh"
        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for name in files:
                if name == file:
                    abs_path = os.path.abspath(os.path.join(root, name))
        result = subprocess.run(
            [
                "sh",
                f"{abs_path}",
                f"{self.args.url}",
                f"{self.args.user}",
                f"{self.args.port}",
                f"{self.args.password}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return result.stdout


def add_parser(subparsers, parent_parser):
    HELP = "Initialise ssh remote bucket"

    parser = subparsers.add_parser(
        "sshremote",
        parents=[parent_parser],
        description="This is command is used to initialise ssh remote bucket",
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
        "--user",
        required=True,
        help="Specify user",
        metavar="<user>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--port",
        required=True,
        help="Specify Port",
        metavar="<port>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--password",
        required=True,
        help="Specify password. This will be saved only on local",
        metavar="<password>",
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

    parser.set_defaults(func=CmdInitSSHRemote)
