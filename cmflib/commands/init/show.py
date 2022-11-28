#!/usr/bin/env python3
import argparse
import os
import subprocess
import shlex

from cmflib import cmfquery
from cmflib.cli.command import CmdBase


class CmdInitShow(CmdBase):
    def run(self):
        result = subprocess.run(
            ["dvc", "config", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(result.stdout)
        return 0


def add_parser(subparsers, parent_parser):
    HELP = "Show cmf config"

    parser = subparsers.add_parser(
        "show",
        parents=[parent_parser],
        description="This command is to show cmf config",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.set_defaults(func=CmdInitShow)
