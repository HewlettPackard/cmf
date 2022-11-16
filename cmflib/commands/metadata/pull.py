#!/usr/bin/env python3
import argparse
import json
import os
from cmflib import merger
from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdMetadataPull(CmdBase):
    def run(self):
        url = "http://127.0.0.1:80"
        mlmd_json=server_interface.call_mlmd_pull(url)

        if self.args.file_name:
            directory_to_dump=self.args.file_name
        else:
            directory_to_dump = os.getcwd()
        cmd='pull'
        merger.parse_json_to_mlmd(mlmd_json.content,directory_to_dump+'/mlmd',cmd)
        return 0

def add_parser(subparsers, parent_parser):
    PULL_HELP = "Pull is user-generated to fetch mlmd from server to local "

    parser = subparsers.add_parser(
        "pull",
        parents=[parent_parser],
        description="This is pull command",
        help=PULL_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "-P",
        "--pipeline_name",
        required=True,
        help="Specify Pipeline name",
        metavar="<pipeline_name>"
    )

    parser.add_argument(
        "-F",
        "--file_name",
        help="Specify location to pull mlmd file",
        metavar="<file_name>"
    )

    parser.set_defaults(func=CmdMetadataPull)
