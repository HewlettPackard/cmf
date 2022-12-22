#!/usr/bin/env python3
import argparse
import os
import subprocess

from cmflib.cli.command import CmdBase
from cmflib.cli.utils import check_minio_server
from cmflib.dvc_config import dvc_config


class CmdArtifactPush(CmdBase):
    def run(self):
        dvc_config_op = dvc_config.get_dvc_config()
        if(dvc_config_op[0] == "minio"):
            if(check_minio_server() == "SUCCESS"):
                result = subprocess.run(["dvc", "push"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                return result.stdout
            else:
                return check_minio_server()
        else:
            result = subprocess.run(["dvc", "push"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return result.stdout


def add_parser(subparsers, parent_parser):
    HELP = "Push artifacts to local/remote repo"

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push artifacts to local/remote repo",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.set_defaults(func=CmdArtifactPush)
