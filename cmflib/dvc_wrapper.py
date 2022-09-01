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
        print(f"dvc.exceptions.PathMissingError Caught Unexpected {err}, {type(err)}")
    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
    return c_hash


def git_get_commit() -> str:
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
    try:
        process = subprocess.Popen(['git', 'add', file_path],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # To-Do : Parse the output and report if error
        _, _ = process.communicate(timeout=60)
        process = subprocess.Popen(['git', 'commit', '-m ' + 'commiting ' + str(file_path) + "-" + str(execution_id)],
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


def commit_output(folder: str, execution_id: str) -> str:
    commit = ""
    try:
        process = subprocess.Popen(['dvc', 'add', folder],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        # To-Do : Parse the output and report if error
        output, errs = process.communicate(timeout=60)
        commit = output.strip()
        process = subprocess.Popen(['git', 'add', folder + '.dvc'],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        # To-Do : Parse the output and report if error
        _, _ = process.communicate(timeout=60)
        process = subprocess.Popen(['git', 'commit', '-m ' + 'commiting ' + str(folder) + "-" + str(execution_id)],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)

        output, errs = process.communicate(timeout=60)
        commit = output.strip()

        process = subprocess.Popen(['git', 'log', folder + '.dvc'],
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


# Get the remote repo
def git_get_repo() -> str:
    commit = ""
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
