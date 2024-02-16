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
import subprocess
import dvc.api
import dvc.exceptions


def check_git_remote() -> bool:
    process = ""
    commit = ""
    git_remote_configured = False
    try:
        process = subprocess.Popen(['git', 'remote', 'show'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # output = process.stdout.readline()
        output, error = process.communicate(timeout=60)

        remote = output.strip()
        if remote:
            git_remote_configured = True
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
    return git_remote_configured


def check_default_remote() -> bool:
    process = ""
    commit = ""
    dvc_configured = False
    try:
        process = subprocess.Popen(['dvc', 'config', 'core.remote'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # output = process.stdout.readline()
        output, error = process.communicate(timeout=60)

        remote = output.strip()
        if remote:
            dvc_configured = True
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
    return dvc_configured


def dvc_get_url(folder: str, retry: bool = False, repo: str = "") -> str:
    url = ""
    try:
        if not repo and not repo.isspace():
            url = dvc.api.get_url(folder)
        else:
            url = dvc.api.get_url(folder, repo)
    except dvc.exceptions.PathMissingError as err:
        if not retry:
            print(f"Retrying with full path")
            folder = os.path.join(os.getcwd(), folder)
            url = dvc_get_url(folder, True)
        else:
            print(f"dvc.exceptions.PathMissingError Caught  Unexpected {err}, {type(err)}")
    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
    return url


def dvc_get_hash(folder: str, repo: str = "") -> str:
    c_hash = ""
    try:
        url = dvc_get_url(folder, False, repo)
        url_list = url.split('/')
        len_list = len(url_list)
        c_hash = ''.join(url_list[len_list - 2:len_list])

    except dvc.exceptions.PathMissingError as err:
        print(f"dvc.exceptions.PathMissingError Caught  Unexpected {err}, {type(err)}")
    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
    return c_hash


def check_git_repo() -> bool:

    process = ""
    commit = ""
    is_git_repo = False
    try:
        process = subprocess.Popen(['git',
                                    'rev-parse',
                                    '--is-inside-work-tree'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        # output = process.stdout.readline()
        output, error = process.communicate(timeout=60)

        is_git_repo = output.strip()
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
    return is_git_repo


def git_checkout_new_branch(branch_name: str):

    process = ""
    commit = ""
    try:
        process = subprocess.Popen(['git',
                                    'checkout',
                                    '-q',
                                    '-B',
                                    branch_name],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # output = process.stdout.readline()
        output, error = process.communicate(timeout=60)

        commit = output.strip()
        print(f"*** Note: CMF will check out a new branch in git to commit the metadata files ***\n"
              f"*** The checked out branch is {branch_name}. ***")
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
        print(f"Unexpected {err}, {type(err)}")
        print(f"Unexpected {outs}")
        print(f"Unexpected {errs}")
        print(f"Checking out new branch for the execution failed, continuing in the default branch.")


def git_get_commit() -> str:
    process = ""
    commit = ""
    try:
        process = subprocess.Popen(['git', 'rev-parse', 'HEAD'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # output = process.stdout.readline()
        output, error = process.communicate(timeout=60)
        commit = output.strip()
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
        print(f"Unexpected {err}, {type(err)}")
        print(f"Unexpected {outs}")
        print(f"Unexpected {errs}")
    return commit


def commit_dvc_lock_file(file_path: str, execution_id) -> str:
    commit = ""
    process = ""
    try:
        process = subprocess.Popen(['git', 'add', file_path],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # To-Do : Parse the output and report if error
        _, _ = process.communicate(timeout=60)
        process = subprocess.Popen(
            [
                'git',
                'commit',
                '-m ' +
                'commiting ' +
                str(file_path) +
                "-" +
                str(execution_id)],
            stdout=subprocess.PIPE,
            universal_newlines=True)

        output, errs = process.communicate(timeout=60)
        commit = output.strip()
        process = subprocess.Popen(['git', 'log', file_path],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # To-Do : Parse the output and report if error
        output, errs = process.communicate(timeout=60)
        commit = output.splitlines()[0].strip()
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
        print(f"Unexpected {err}, {type(err)}")
        print(f"Unexpected {outs}")
        print(f"Unexpected {errs}")
    return commit

def git_commit(execution_id: str) -> str:
    commit = ""
    process = None
    try:
        # To-Do : Parse the output and report if error
        process = subprocess.Popen(['git', 'commit', '-m ' + 'commiting ' + str(execution_id)],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        output, errs = process.communicate(timeout=60)
        commit = output.strip()

        process = subprocess.Popen(['git', 'log'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # To-Do : Parse the output and report if error
        output, errs = process.communicate(timeout=60)
        commit = output.splitlines()[0].strip()
    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit

def commit_output(folder: str, execution_id: str) -> str:
    commit = ""
    process = ""
    try:
        process = subprocess.Popen(['dvc', 'add', folder],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        # To-Do : Parse the output and report if error
        output, errs = process.communicate()
        commit = output.strip()
        process = subprocess.Popen(['git', 'add', folder + '.dvc'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # To-Do : Parse the output and report if error
        _, _ = process.communicate(timeout=60)
        # process = subprocess.Popen(
        #     [
        #         'git',
        #         'commit',
        #         '-m ' +
        #         'commiting dvc metadata file for ' +
        #         str(folder) +
        #         "-" +
        #         str(execution_id)],
        #     stdout=subprocess.PIPE,
        #     universal_newlines=True)
        # 
        # output, errs = process.communicate(timeout=60)
        # commit = output.strip()
        # 
        # process = subprocess.Popen(['git', 'log', folder + '.dvc'],
        #                            stdout=subprocess.PIPE,
        #                            universal_newlines=True)
        # To-Do : Parse the output and report if error
        # output, errs = process.communicate(timeout=60)
        # commit = output.splitlines()[0].strip()
    except Exception as err:
        process.kill()
        outs, errs = process.communicate()
        print(f"Unexpected {err}, {type(err)}")
        print(f"Unexpected {outs}")
        print(f"Unexpected {errs}")
    return commit


# Get the remote repo
def git_get_repo() -> str:
    commit = ""
    process = ""
    output = ""
    errs = ""
    try:
        process = subprocess.Popen(['git', 'remote', '-v'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        process.kill()
        print(f"Unexpected {err}, {type(err)}")
        print(f"Unexpected {output}")
        print(f"Unexpected {errs}")
    return commit.split()[1]

#Initialise git with quiet option
def git_quiet_init() -> str:
    commit = ""
    try:
        process = subprocess.Popen(['git', 'init', '-q'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit


# Initial git commit
def git_initial_commit() -> str:
    commit = ""
    try:
        process = subprocess.Popen(['git', 'commit', '-q', '--allow-empty', '-n', '-m', "Initial code commit"],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit

# Add a remote repo url
def git_add_remote(git_url) -> str:
    commit = ""
    try:
        process = subprocess.Popen(['git', 'remote', 'add', 'cmf_origin', f"{git_url}"],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit

# dvc init with quiet option
def dvc_quiet_init() -> str:
    commit = ""
    try:
        process = subprocess.Popen(['dvc', 'init', '-q'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit

# add repo in dvc
def dvc_add_remote_repo(repo_type, repo_path) -> str:
    commit = ""
    try:
        process = subprocess.Popen(['dvc', 'remote', 'add', '-d', '-f', f"{repo_type}", f"{repo_path}"],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit

# add repo related attributes in dvc
def dvc_add_attribute(repo_type, attribute_type, attribute_value) -> str:
    commit = ""
    try:
        process = subprocess.Popen(['dvc', 'remote', 'modify', f"{repo_type}", f"{attribute_type}", f"{attribute_value}"],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit


# get dvc config
def dvc_get_config() -> str:
    commit = ""
    try:
        process = subprocess.Popen(['dvc','config', '-l'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate(timeout=60)
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit


# dvc push
def dvc_push() -> str:
    commit = ""
    try:
        process = subprocess.Popen(['dvc', 'push'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        output, errs = process.communicate()
        commit = output.strip()

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        if isinstance(object, subprocess.Popen):
           process.kill()
           outs, errs = process.communicate()
           print(f"Unexpected {outs}")
           print(f"Unexpected {errs}")
    return commit
