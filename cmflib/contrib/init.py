###
# Copyright (2022) Hewlett Packard Enterprise Development LP
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

import os
import uuid
import click

@click.command()
@click.argument("project_path", required=False, default=os.getcwd(), type=str)
@click.option("--user_name", required=False, envvar="GIT_USER_NAME", default="First Second", type=str)
@click.option("--user_email", required=False, envvar="GIT_USER_EMAIL", default="first.second@corp.org", type=str)
@click.option(
    "--git_remote",
    required=False,
    envvar="GIT_REMOTE_URL",
    type=str,
    default="git@github.com:first-second/experiment-repo.git",
)
@click.option(
    "--dvc_remote",
    required=False,
    envvar="DVC_REMOTE_URL",
    type=str,
    default=f'/tmp/cmf/dvc_remotes/{str(uuid.uuid4()).replace("-", "")}',
)
def init_cmf_project(project_path: str, user_name: str, user_email: str, git_remote: str, dvc_remote: str):
    """Helper python script to init a new CMF project.

    Pre-requisites: `git` and `dvc` must be installed in a system.

    Args:
        project_path: Path to the new project. It must exist and probably must be empty.
        user_name: Username to init git repository.
        user_email: User email to init git repository.
        git_remote: Git remote to set on a new git repository.
        dvc_remote: DVC remote to set on a new git repository (dvc will be initialized too).
    """
    os.chdir(project_path)

    print("[1/4] [GIT/DVC INIT  ] executing git init and dvc init.")
    os.system("git init -q")
    os.system("dvc init -q")
    os.system(f'git config --global user.name "{user_name}"')
    os.system(f'git config --global user.email "{user_email}"')

    print("[2/4] [INITIAL COMMIT] performing initial blank commit into main.")
    os.system("git checkout -b master")
    os.system('git commit --allow-empty -n -m "Initial code commit"')

    print(f"[3/4] [GIT REMOTE    ] setting git remote to {git_remote}")
    os.system(f'git remote add origin "${git_remote}"')

    print(f"[4/4] [DVC REMOTE    ] setting dvc remote to ${dvc_remote}")
    os.system(f'dvc remote add myremote -f "${dvc_remote}"')
    os.system("dvc remote default myremote")


if __name__ == "__main__":
    init_cmf_project()
