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

#        temp_path = data.get("server_store_path", "")

        #export server_store_path
 #       if not temp_path:
  #          export_com = f"export server_store_path={temp_path}"
   #         subprocess.run(export_com, shell=True) # replace this with the os.environ variable #warning is needed

        cmf_server_url = data.get("cmf_server_url", "")

        if not cmf_server_url:
            print("Please provide cmf-server-url in config.json")
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

    except Exception as e:
        print(f"An error occurred: {e}")



