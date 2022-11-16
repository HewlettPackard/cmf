#!/usr/bin/env python3
import argparse
import os

from cmflib import cmfquery
from cmflib.cli.command import CmdBase
from cmflib.request_mlmdserver import server_interface


class CmdInitAmazonS3(CmdBase):
    def run(self):
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Used to initialise amazon S3 bucket"

    parser = subparsers.add_parser(
        "amazonS3",
        parents=[parent_parser],
        description="This is command is used to initialise amazon S3 bucket",
        help=HELP,
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

    parser.set_defaults(func=CmdInitAmazonS3)
