#!/usr/bin/env python3
import argparse
import os
import requests

from cmflib import cmfquery
from cmflib import minio_artifacts
from cmflib.cli.command import CmdBase
from cmflib.cli import utils


class CmdPush(CmdBase):
    def run(self):
        # Put a check to see whether pipline exists or not
        current_directory = os.getcwd()
        mlmd_file_name = "./mlmd"
        if self.args.file_name:
            mlmd_file_name = self.args.file_name
            current_directory = os.path.dirname(self.args.file_name)
        if not os.path.exists(mlmd_file_name):
            return f"{mlmd_file_name} doesn't exists in current directory"
        query = cmfquery.CmfQuery(mlmd_file_name)
        data = utils.read_cmf_config()
        # print(type(data))
        server_address = f"http://{data[0]['Server']['IP']}:{data[0]['Server']['Port']}"
        print(server_address)
        try:
            response = requests.get(server_address)
            print(response.status_code)
        except Exception as exec:
            print(exec)
        return 0


def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Push user-generated mlmd to server to create one true mlmd file for every pipeline"

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="This is push command",
        help=PUSH_HELP,
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
        help="Specify mlmd file name",
        metavar="<file_name>"
    )

    parser.set_defaults(func=CmdPush)
