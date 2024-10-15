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
import subprocess
import requests

from cmflib.cli.command import CmdBase
from cmflib.dvc_wrapper import dvc_get_config, git_get_repo, git_checkout_new_branch


class CmdRepoPush(CmdBase):
    def branch_exists(self, repo_own, repo_name, branch_name):
        url = f"https://api.github.com/repos/{repo_own}/{repo_name}/branches/{branch_name}"
        res = requests.get(url)

        if res.status_code == 200:
            return True
        return False


    def run_command(self, command, cwd=None):
        process = subprocess.Popen(command, cwd=cwd, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return (stdout.decode('utf-8').strip() if stdout else '',
                stderr.decode('utf-8').strip() if stderr else '',
                process.returncode)
    

    def run(self):
        msg = "'cmf' is not configured.\nExecute 'cmf init' command."
        result = dvc_get_config()
        if len(result) == 0:
            return msg
        else:    
            # checking if the current branch is cmf_origin or not
            if "mlmd" in self.run_command("git branch")[0]:    
                url = git_get_repo()
                if self.branch_exists(url.split("/")[-2], url.split("/")[-1], "mlmd"):
                    # pull the code
                    # push the code
                    stdout, stderr, returncode = self.run_command("git pull cmf_origin mlmd")
                    # print(returncode+"1")
                    if returncode != 0:
                        return f"Error pulling changes: {stderr}"
            
                    stdout, stderr, returncode = self.run_command("git push -u cmf_origin mlmd")
                    if returncode != 0:
                        return f"Error pushing changes: {stderr}"

                    return "Successfully pushed and pulled changes!"
                else:
                    # push the code
                    stdout, stderr, returncode = self.run_command("git push -u cmf_origin mlmd")
                    if returncode != 0:
                        return f"Error pushing changes: {stderr}"
                    return "Successfully pushed and pulled changes!"
            else:
                if self.args.file_name:
                    git_checkout_new_branch(self.args.file_name)
                else:
                    git_checkout_new_branch("mlmd")
                return "Checking out new branch"
    

def add_parser(subparsers, parent_parser):
    PUSH_HELP = "Push user-generated mlmd to server to create one single mlmd file for all the pipelines."

    parser = subparsers.add_parser(
        "push",
        parents=[parent_parser],
        description="Push user's mlmd to cmf-server.",
        help=PUSH_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-f", "--file_name", help="Specify mlmd file name.", metavar="<file_name>"
    )

    parser.set_defaults(func=CmdRepoPush)
