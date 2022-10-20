#!/usr/bin/env python3
import argparse
import os

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdMetadataPush(CmdBase):
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
        json_payload = query.dumptojson(self.args.pipeline_name)
        url = "http://127.0.0.1:80"
        # Get url from config
        # print(json_payload)
        status_code = server_interface.call_mlmd_push(json_payload, url)
        return 0


def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Push user-generated mlmd to server to create one single mlmd file for all the pipeline"

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

    parser.set_defaults(func=CmdMetadataPush)
