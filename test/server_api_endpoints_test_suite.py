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

import pytest
import os
import sys
import json
import shutil
import subprocess

if __name__ == "__main__":
    try:
        # Specify the path to your JSON file
        json_file_path = 'config.json'

        # Open the file for reading
        with open(json_file_path, 'r') as file:
        # Load the JSON data from the file
            data = json.load(file)

        cmf_server_url = data.get("cmf_server_url", "")

        if not cmf_server_url:
            print("Please provide cmf-server-url in config.json and start test cases again")
            sys.exit(1)    # abnormal script termination

        #run tests for local
        # copy example-get-started
        source_folder = '../examples/example-get-started'
        destination_folder = os.getcwd() #assumption running inside from test folder

        # Using subprocess to execute the cp command
        subprocess.run(['cp', '-r', source_folder, destination_folder])

        os.chdir("./example-get-started")

        command = f"pytest -vs -q  --cmf_server_url={cmf_server_url} ../client/test_local.py"

        result = subprocess.run(command, text=True, shell=True)

        os.chdir("..")
        # Deleting example-get-started folder
        shutil.rmtree("./example-get-started")

        print("/example-get-started deleted")

        # create a root folder /cmf-server/data/static
        root_folder_path = '/cmf-server/data/static'

        # Check if the folder already exists
        if not os.path.exists(root_folder_path):
            # Create the folder if it doesn't exist
            subprocess.run(['sudo','mkdir', '-p', root_folder_path])

        print(f"{root_folder_path} created.")

        file_path = "./cmf-server/data/mlmd" #assumption running inside from test folder
        destination_folder = "/cmf-server/data"

        # copy mlmd file to /cmf-server/data folder for api endpoints testing at the end
        subprocess.run(['sudo','cp', file_path, destination_folder])


        # delete mlmd on file_path
        if os.path.exists(file_path):
            command = f"sudo rm -rf {file_path}"
            result = subprocess.run(command, text=True, shell=True)
            if result.returncode == 0:
                print(f"The file '{file_path}' successfully deleted.")

        # execute test_api_endpoints
        command = f"pytest -vs  ./server/test_api_endpoints.py"
        result = subprocess.run(command, text=True, shell=True)

        # Command to be executed
        command = 'sudo rm -rf /cmf-server'

        try:
            # Run the command using subprocess
            subprocess.run(command, shell=True, check=True)
            print(f"Command '{command}' executed successfully.")
        except subprocess.CalledProcessError as e:
            # Handle any errors that occur during the execution
            print(f"Error executing command '{command}': {e}")



    except Exception as e:
        print(f"An error occurred: {e}")

