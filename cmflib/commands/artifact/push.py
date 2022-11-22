#!/usr/bin/env python3
import argparse
import os
import subprocess

from cmflib.cli.command import CmdBase


class CmdArtifactPush(CmdBase):
    def run(self):
        result = subprocess.run(["dvc", "push"], capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        return 0


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
