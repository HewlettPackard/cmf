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
import json
import requests
import subprocess

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

def get_python_env(env_name='cmf'):
    # what this is supposed to return 
    try:
        # Check if the environment is conda
        if is_conda_installed():  # If conda is installed and the command succeeds

            # Step 1: Get the list of conda packages
            conda_packages = subprocess.check_output(['conda', 'list', '--export']).decode('utf-8').splitlines()

            # Step 2: Get the list of pip packages
            pip_packages = subprocess.check_output(['pip', 'freeze']).decode('utf-8').splitlines()

            # Step 3: Get the list of channels from the current conda environment
            channels_raw = subprocess.check_output(['conda', 'config', '--show', 'channels']).decode('utf-8').splitlines()

            # Filter out lines that start with 'channels:' and any empty or commented lines
            channels = [line.strip().lstrip('- ').strip() for line in channels_raw if line and not line.startswith('channels:') and not line.startswith('#')]

            # Step 4: Create a YAML structure for the environment
            env_data = {
                'name': env_name,  # Name the environment -- don't provide the name 
                'channels': channels,  # Add the cleaned channels list
                'dependencies': [],
            }

            # Add conda packages to dependencies
            for package in conda_packages:
                if not package.startswith('#') and len(package.strip()) > 0:
                    env_data['dependencies'].append(package)

            # Add pip packages under a pip section in dependencies
            if pip_packages:
                pip_section = {'pip': pip_packages}
                env_data['dependencies'].append(pip_section)

            return env_data

        else:
            # If not conda, assume virtualenv/pip
            # Step 1: Get the list of pip packages
            pip_packages = subprocess.check_output(['pip', 'freeze']).decode('utf-8').splitlines()

            return pip_packages

    except Exception as e:
        print(f"An error occurred: {e}")

    return

def get_md5_hash(output):
    import hashlib

    # Convert the string to bytes (utf-8 encoding)
    byte_content = output.encode('utf-8')

    # Create an MD5 hash object
    md5_hash = hashlib.md5()

    # Update the hash with the byte content
    md5_hash.update(byte_content)

    # Return the hexadecimal digest
    hash_for_op = md5_hash.hexdigest()

    return hash_for_op
        
def change_dir(cmf_init_path):
    logging_dir = os.getcwd()
    if not logging_dir == cmf_init_path:
        os.chdir(cmf_init_path)
    return logging_dir


def is_conda_installed() -> bool:
    """Check if Conda is installed by running 'conda --version'."""
    try:
        # Run the 'conda --version' command and capture the output
        subprocess.run(['conda', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def list_conda_packages_json() -> list:
    """Return a list of installed Conda packages and their versions."""
    try:
        result = subprocess.run(['conda', 'list', '--json'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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

def branch_exists(repo_owner: str, repo_name: str, branch_name: str) -> bool:
    """
    Check if a branch exists in a GitHub repository.

    Args:
        repo_owner: The owner of the GitHub repository.
        repo_name: The name of the GitHub repository.
        branch_name: The name of the branch to check.

    Returns:
        bool: True if the branch exists, otherwise False.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches/{branch_name}"
    res = requests.get(url)

    if res.status_code == 200:
        return True
    return False