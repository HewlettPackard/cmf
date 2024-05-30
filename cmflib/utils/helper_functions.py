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

import os
import sys
import subprocess
import json

def is_git_repo():
    git_dir = os.path.join(os.getcwd(), '.git')
    print("git_dir", git_dir)
    result = os.path.exists(git_dir) and os.path.isdir(git_dir)
    if result:
        return f"A Git repository already exists in {git_dir}."
    else:
        return


def get_python_env()-> str:
    installed_packages = ""
    python_version = sys.version
    packages = ""
    # check if conda is installed
    if is_conda_installed():
        import conda
        # List all installed packages and their versions
        data = list_conda_packages_json()
        transformed_result = [f"{entry['name']}=={entry['version']}" for entry in data]
        installed_packages =  transformed_result
        packages = f"Conda: Python {python_version}: {installed_packages}"
    else:
        # pip
        try:
            from pip._internal.operations import freeze

            # List all installed packages and their versions
            installed_packages_generator = freeze.freeze()
            installed_packages = list(installed_packages_generator)
            packages = f"Python {python_version}: {installed_packages}"
        except ImportError:
            print("Pip is not installed.")
    return packages

def change_dir(cmf_init_path):
    logging_dir = os.getcwd()
    if not logging_dir == cmf_init_path:
        os.chdir(cmf_init_path)
    return logging_dir

def is_conda_installed():
    try:
        import conda
        # Run the 'conda --version' command and capture the output
        subprocess.run(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
    except ImportError:
        return False


def list_conda_packages_json():
    try:
        result = subprocess.run(['conda', 'list', '--json'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


