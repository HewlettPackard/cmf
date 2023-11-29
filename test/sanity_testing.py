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
        ssh_path = data.get("ssh_path", "")
        ssh_user = data.get("ssh_user", "")
        ssh_pass = data.get("ssh_password", "")

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

        file_path = "./cmf-server/data/mlmd"
        # delete mlmd pushed on server
        try:
            # Attempt to delete the file
            os.remove(file_path)
            print(f"The file '{file_path}' has been deleted.")
        except FileNotFoundError:
          # Handle the case where the file does not exist
            print(f"The file '{file_path}' does not exist.")
        except Exception as e:
           # Handle other exceptions
            print(f"An error occurred: {e}")


        # run test for minioS3
        source_folder = '../examples/example-get-started'
        destination_folder = os.getcwd() #assumption running inside from test folder

        # Using subprocess to execute the cp command
        subprocess.run(['cp', '-r', source_folder, destination_folder])

        os.chdir("./example-get-started")

        command = f"pytest -vs -q  --cmf_server_url={cmf_server_url} ../client/test_minios3.py"

        result = subprocess.run(command, text=True, shell=True)

        os.chdir("..")
        # Deleting example-get-started folder
        shutil.rmtree("./example-get-started")

        file_path = "./cmf-server/data/mlmd"
        # delete mlmd pushed on server
        try:
            # Attempt to delete the file
            os.remove(file_path)
            print(f"The file '{file_path}' has been deleted.")
        except FileNotFoundError:
          # Handle the case where the file does not exist
            print(f"The file '{file_path}' does not exist.")
        except Exception as e:
           # Handle other exceptions
            print(f"An error occurred: {e}")


        # run tests for ssh remote
        if not ssh_path and not ssh_user and not ssh_pass:
            print("Please provide ssh_path, ssh_user and ssh_password in config.json and start test cases again.")
            sys.exit(1)
        source_folder = '../examples/example-get-started'
        destination_folder = os.getcwd() #assumption running inside from test folder

        # Using subprocess to execute the cp command
        subprocess.run(['cp', '-r', source_folder, destination_folder])

        os.chdir("./example-get-started")


        command = f"pytest -vs -q  --cmf_server_url={cmf_server_url} --ssh_path={ssh_path} --ssh_user={ssh_user} --ssh_pass={ssh_pass} ../client/test_sshremote.py"

        result = subprocess.run(command, text=True, shell=True)

        os.chdir("..")
        # Deleting example-get-started folder
        shutil.rmtree("./example-get-started")

        file_path = "./cmf-server/data/mlmd"
        # delete mlmd pushed on server
        try:
            # Attempt to delete the file
            os.remove(file_path)
            print(f"The file '{file_path}' has been deleted.")
        except FileNotFoundError:
          # Handle the case where the file does not exist
            print(f"The file '{file_path}' does not exist.")
        except Exception as e:
           # Handle other exceptions
            print(f"An error occurred: {e}")



    except Exception as e:
        print(f"An error occurred: {e}")



