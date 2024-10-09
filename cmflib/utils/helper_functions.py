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
import yaml

def is_url(url)-> bool:
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

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
        conda_packages = list_conda_packages_json()
        installed_packages = [f"{pkg['name']}=={pkg['version']}" for pkg in conda_packages]
        env_info = {
            'Package Manager': 'Conda',
            'Python Version': python_version,
            'Installed Packages': installed_packages
        }
    else:
        # Fallback to pip if conda is not available
        try:
            from pip._internal.operations import freeze
            # List all installed packages and their versions
            installed_packages_generator = freeze.freeze()
            print(type(installed_packages_generator))
            installed_packages = list(installed_packages_generator)
            env_info = yaml.dump(installed_packages)
            #env_info = f"Python {python_version}: {installed_packages}"
        except ImportError:
            print("Pip is not installed.")

    # Convert the result to YAML
    yaml_output = yaml.dump(env_info, sort_keys=False)
    return yaml_output

'''
def get_python_env() -> str:
    """Return Python environment information including version and installed packages in YAML format."""
    python_version = sys.version
    installed_packages = {}

    # Check if conda is installed
    if is_conda_installed():
        import conda
        # List all installed Conda packages
        conda_packages = list_conda_packages_json()
        installed_packages = {pkg['name']: pkg['version'] for pkg in conda_packages}
        env_info = {
            'Package Manager': 'Conda',
            'Python Version': python_version,
            'Installed Packages': installed_packages
        }
    else:
        # Fallback to pip if Conda is not available
        try:
            from pip._internal.operations import freeze
            # List all installed pip packages
            installed_packages_generator = freeze.freeze()
            installed_packages = {pkg.split('==')[0]: pkg.split('==')[1] for pkg in installed_packages_generator}
            env_info = {
                'Package Manager': 'Pip',
                'Python Version': python_version,
                'Installed Packages': installed_packages
            }
        except ImportError:
            env_info = {
                'Error': 'Pip is not installed, and Conda is not available.'
            }

    # Convert the result to YAML
    yaml_output = yaml.dump(env_info, sort_keys=False)
    return yaml_output
'''

def change_dir(cmf_init_path):
    logging_dir = os.getcwd()
    if not logging_dir == cmf_init_path:
        os.chdir(cmf_init_path)
    return logging_dir


def is_conda_installed() -> bool:
    """Check if Conda is installed by running 'conda --version'."""
    try:
        subprocess.run(["conda", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def list_conda_packages_json() -> list:
    """Return a list of installed Conda packages and their versions."""
    try:
        result = subprocess.run(["conda", "list", "--json"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return []


# Generate SciToken dynamically 
def generate_osdf_token(key_id, key_path, key_issuer) -> str:

    #for SciToken Generation & Validation
    import scitokens
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    dynamic_pass="" #Initialize Blank dynamic Password

    #Read Private Key using load_pem_private_key() method 
    if not os.path.exists(key_path):
        print(f"File {key_path} does not exist.")
        return dynamic_pass

    try:
        with open(key_path, "r") as file_pointer:
            private_key_contents = file_pointer.read()

        loaded_private_key = serialization.load_pem_private_key(
            private_key_contents.encode(),
            password=None, # Assumes Private key. Update this if password is used for Private Key
            backend=default_backend()
        )

        if is_url(key_issuer):
            token = scitokens.SciToken(key=loaded_private_key, key_id=key_id) #Generate SciToken
            #token.update_claims({"iss": key_issuer, "scope": "write:/ read:/", "aud": "NRP", "sub": "NRP"})
            token.update_claims({"scope": "write:/ read:/", "aud": "NRP", "sub": "NRP"}) #TODO: Figure out how to supply these as input params

            # Serialize the token to a string
            token_ser = token.serialize(issuer=key_issuer) 
            #Key_issuer is something like ""https://t.nationalresearchplatform.org/fdp"

            #Stringify token_str
            token_str=token_ser.decode()
            dynamic_pass="Bearer "+ token_str
        else:
            print(f"{key_issuer} is not a valid URL.")

    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")

    return dynamic_pass