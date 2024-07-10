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
from cmflib.utils.helper_functions import generate_osdf_token
from cmflib.utils.helper_functions import is_url
from cmflib.utils.dvc_config import DvcConfig
from cmflib.dvc_wrapper import dvc_push
from cmflib.dvc_wrapper import dvc_add_attribute
from cmflib.utils.cmf_config import CmfConfig

class CmdArtifactPush(CmdBase):
    def run(self):
        result = ""
        dvc_config_op = DvcConfig.get_dvc_config()
        cmf_config_file = os.environ.get("CONFIG_FILE", ".cmfconfig")
        cmf_config={}
        cmf_config=CmfConfig.read_config(cmf_config_file)
        out_msg = check_minio_server(dvc_config_op)
        if dvc_config_op["core.remote"] == "minio" and out_msg != "SUCCESS":
            return out_msg
        elif dvc_config_op["core.remote"] == "osdf":
            #print("key_id="+cmf_config["osdf-key_id"])       
            dynamic_password = generate_osdf_token(cmf_config["osdf-key_id"],cmf_config["osdf-key_path"],cmf_config["osdf-key_issuer"])
            #print("Dynamic Password"+dynamic_password)
            dvc_add_attribute(dvc_config_op["core.remote"],"password",dynamic_password)
            #The Push URL will be something like: https://<Path>/files/md5/[First Two of MD5 Hash]
            result = dvc_push()
            #print(result)
            return result
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
