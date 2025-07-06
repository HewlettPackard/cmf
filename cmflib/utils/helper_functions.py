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
import readchar
import requests
import textwrap
import subprocess
import hashlib
import sys
import pandas as pd

from tabulate import tabulate
from cmflib.cli.utils import find_root
from cmflib.utils.dvc_config import DvcConfig
from cmflib.cmf_exception_handling import CmfNotConfigured

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
    # Determine the type of Python environment and return its details
    try:
        # Check if the environment is a Conda environment
        if os.getenv('CONDA_PREFIX') is not None:  # If Conda is activated

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
    # Error: Skipping analyzing "scitokens": module is installed, but missing library stubs or py.typed marker
    import scitokens    # type: ignore
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


def display_table(df: pd.DataFrame, columns: list) -> None:
    """
    Display the DataFrame in a paginated table format with text wrapping for better readability.
    Parameters:
    - df: The DataFrame to display.
    - columns: The columns to display in the table.
    """
    # Rearranging columns
    df = df[columns]
    df = df.copy()
    
    # Wrap text in object-type columns to a width of 14 characters.
    # This ensures that long strings are displayed neatly within the table.
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: textwrap.fill(x, width=14) if isinstance(x, str) else x)

    total_records = len(df)
    start_index = 0  

    # Display up to 20 records per page for better readability. 
    # This avoids overwhelming the user with too much data at once, especially for larger mlmd files.
    while True:
        end_index = start_index + 20
        records_per_page = df.iloc[start_index:end_index]
        
        # Display the table.
        # Fix mypy warning by converting DataFrame to list of lists and columns to list of strings.
        table = tabulate(
            records_per_page.values.tolist(),  # Convert DataFrame to list of lists for tabulate
            headers=[str(col) for col in df.columns],  # Ensure headers are list of strings
            tablefmt="grid",
            showindex=False,
        )
        print(table)

        # Check if we've reached the end of the records.
        if end_index >= total_records:
            print("\nEnd of records.")
            break

        # Ask the user for input to navigate pages.
        print("Press any key to see more or 'q' to quit: ", end="", flush=True)
        user_input = readchar.readchar()
        if user_input.lower() == 'q':
            break
        
        # Update start index for the next page.
        start_index = end_index 


def fetch_cmf_config_path() -> tuple[dict, str]: 
    """ Fetches the CMF configuration and its file path.
    Returns: 
        tuple[dict, str]: A tuple containing the DVC configuration (dict) and the CMF config file path (str).
    Raises: 
        CmfNotConfigured: If the CMF configuration is missing or not properly set up.
    """
    # User can provide different name for cmf configuration file using CONFIG_FILE environment variable.
    # If CONFIG_FILE is not provided, default file name is .cmfconfig
    cmf_config = os.environ.get("CONFIG_FILE", ".cmfconfig") 
    error_message = "'cmf' is not configured.\nExecute 'cmf init' command."
    
    # Fetch DVC configuration 
    dvc_output = DvcConfig.get_dvc_config() 
    if not isinstance(dvc_output, dict): 
        raise CmfNotConfigured(error_message)
    
    # Find the root directory containing the CMF config file 
    cmf_config_root = find_root(cmf_config) 
    if "'cmf' is not configured" in cmf_config_root: 
        raise CmfNotConfigured(error_message)
    
    # Construct the full path to the configuration file 
    config_file_path = os.path.join(cmf_config_root, cmf_config)
    return dvc_output, config_file_path


def get_postgres_config() -> dict:
    """
    Get PostgreSQL configuration from environment variables.

    Returns:
        dict: A dictionary containing PostgreSQL configuration.
    """
    IP = os.getenv('MYIP')
    HOSTNAME = os.getenv('HOSTNAME')
    HOST = ""
    if(HOSTNAME!="localhost"):
        HOST = HOSTNAME if HOSTNAME else ""
    else:
        HOST = IP if IP else ""
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    config_dict = {"host":HOST, "port":"5432", "user": POSTGRES_USER, "password": POSTGRES_PASSWORD, "dbname": POSTGRES_DB}
    #print("config_dict = ", config_dict)
    return config_dict


def calculate_md5(file_path):
    """
    Calculate MD5 hash for a file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: MD5 hash of the file
    """
    # Check if file exists
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
        
    # Calculate MD5 hash
    md5_hash = hashlib.md5()
    
    # Read file in chunks to handle large files efficiently
    with open(file_path, 'rb') as file:
        # Read in 4MB chunks
        for chunk in iter(lambda: file.read(4096 * 1024), b''):
            md5_hash.update(chunk)
            
    # Return the hexadecimal digest
    return md5_hash.hexdigest()
