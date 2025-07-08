###
# Copyright (2024) Hewlett Packard Enterprise Development LP
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

from cmflib.cmf_exception_handling import CmfInitComplete, CmfInitFailed, Neo4jArgumentNotProvided
from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import (
    git_quiet_init,
    git_checkout_new_branch,
    git_initial_commit,
    git_add_remote,
    dvc_quiet_init,
    dvc_add_remote_repo,
    dvc_add_attribute,
)
from cmflib.utils.cmf_config import CmfConfig
from cmflib.utils.helper_functions import is_git_repo
from cmflib.utils.helper_functions import generate_osdf_token

class CmdInitOSDFRemote(CmdBase):
    def run(self, live):
        # User can provide different name for cmf configuration file using CONFIG_FILE environment variable.
        # If CONFIG_FILE is not provided, default file name is .cmfconfig
        cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig")

        attr_dict = {}
        # cmf_server_url is default parameter for cmf init command 
        # if user does not provide cmf-server-url, default value is http://127.0.0.1:80
        attr_dict["server-url"] = self.args.cmf_server_url
        CmfConfig.write_config(cmf_config, "cmf", attr_dict)

        # read --neo4j details and add to the exsting file
        if self.args.neo4j_user and self.args.neo4j_password and self.args.neo4j_uri:
            attr_dict = {}
            attr_dict["user"] = self.args.neo4j_user
            attr_dict["password"] = self.args.neo4j_password
            attr_dict["uri"] = self.args.neo4j_uri
            CmfConfig.write_config(cmf_config, "neo4j", attr_dict, True)
        elif (
            not self.args.neo4j_user
            and not self.args.neo4j_password
            and not self.args.neo4j_uri
        ):
            pass
        else:
            raise Neo4jArgumentNotProvided
        output = is_git_repo()
        if not output:
            branch_name = "master"
            print("Starting git init.")
            git_quiet_init()
            git_checkout_new_branch(branch_name)
            git_initial_commit()
            git_add_remote(self.args.git_remote_url)
            print("git init complete.")

        print("Starting cmf init.")
        repo_type = "osdf"
        dvc_quiet_init()
        output = dvc_add_remote_repo(repo_type, self.args.path)
        if not output:
            raise CmfInitFailed
        print(output)
        #dvc_add_attribute(repo_type, "key_id", self.args.key_id)
        #dvc_add_attribute(repo_type, "key_path", self.args.key_path)
        #dvc_add_attribute(repo_type, "key_issuer", self.args.key_issuer)
        #Writing to an OSDF Remote is based on SSH Remote. With few additions
        #In addition to URL (including FQDN, port, path), we need to provide 
        #method=PUT, ssl_verify=false, ask_password=false, auth=custom, custom_auth-header='Authorization'
        #password='Bearer + dynamically generated scitoken' (This token has a timeout of 15 mins so must be generated right before any push/pull) 
        dvc_add_attribute(repo_type,"method", "PUT")
        dvc_add_attribute(repo_type,"ssl_verify", "false")
        dvc_add_attribute(repo_type,"ask_password", "false")
        dvc_add_attribute(repo_type,"auth", "custom")
        dvc_add_attribute(repo_type,"custom_auth_header", "Authorization")
        dynamic_password = generate_osdf_token(self.args.key_id,self.args.key_path,self.args.key_issuer)
        dvc_add_attribute(repo_type,"password",dynamic_password)

        attr_dict = {}
        attr_dict["path"] = self.args.path
        attr_dict["cache"] = self.args.cache
        attr_dict["key_id"] = self.args.key_id
        attr_dict["key_path"] = self.args.key_path
        attr_dict["key_issuer"] = self.args.key_issuer
        CmfConfig.write_config(cmf_config, "osdf", attr_dict, True)

        return CmfInitComplete


def add_parser(subparsers, parent_parser):
    HELP = "Initialises remote OSDF directory as artifact repository."

    parser = subparsers.add_parser(
        "osdfremote",
        parents=[parent_parser],
        description="This command initialises remote OSDF directory as artifact repository for CMF.",
        help=HELP,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    required_arguments = parser.add_argument_group("required arguments")

    required_arguments.add_argument(
        "--path",
        required=True,
        help="Specify FQDN for OSDF directory path including port and path",
        metavar="<path>",
        default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--cache",
        help="Specify FQDN for OSDF cache path including port and path. For Ex. https://osdf-director.osg-htc.org/nrp/fdp/",
        metavar="<cache>",
        #default="https://osdf-director.osg-htc.org/nrp/fdp/",
        default="",
    )

    required_arguments.add_argument(
        "--key-id",
        required=True,
        help="Specify key_id for provided private key. eg. b2d3",
        metavar="<key_id>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--key-path",
        required=True,
        help="Specify path for private key on local filesystem. eg. ~/.ssh/XXX.pem",
        metavar="<key_path>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--key-issuer",
        required=True,
        help="Specify URL for Key Issuer. eg. https://t.nationalresearchplatform.org/XXX",
        metavar="<key_issuer>",
        default=argparse.SUPPRESS,
    )

    required_arguments.add_argument(
        "--git-remote-url",
        required=True,
        help="Specify git repo url. eg: https://github.com/XXX/example.git",
        metavar="<git_remote_url>",
        default=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--cmf-server-url",
        help="Specify cmf-server URL.",
        metavar="<cmf_server_url>",
        default="http://127.0.0.1:8080",
    )

    parser.add_argument(
        "--neo4j-user",
        help="Specify neo4j user.",
        metavar="<neo4j_user>",
        # default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--neo4j-password",
        help="Specify neo4j password.",
        metavar="<neo4j_password>",
        # default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--neo4j-uri",
        help="Specify neo4j uri.eg bolt://localhost:7687",
        metavar="<neo4j_uri>",
        # default=argparse.SUPPRESS,
    )

    parser.set_defaults(func=CmdInitOSDFRemote)
