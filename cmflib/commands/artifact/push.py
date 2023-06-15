###
# Copyright (2023) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

#!/usr/bin/env python3
import argparse
import os
import subprocess

from cmflib.cli.command import CmdBase
from cmflib.cli.utils import check_minio_server
from cmflib.utils.dvc_config import DvcConfig
from cmflib.dvc_wrapper import dvc_push


class CmdArtifactPush(CmdBase):
    def run(self):
        result = ""
        dvc_config_op = DvcConfig.get_dvc_config()
        out_msg = check_minio_server(dvc_config_op)
        if dvc_config_op["core.remote"] == "minio" and out_msg != "SUCCESS":
            return out_msg
        else:
            result = dvc_push()
            return result


def add_parser(subparsers, parent_parser):
    HELP = "Push artifacts to the user configured artifact repo."

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push artifacts to the user configured artifact repo.",
        help=HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.set_defaults(func=CmdArtifactPush)
